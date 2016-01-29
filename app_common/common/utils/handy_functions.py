__author__ = 'erikfarmer'

import re
import json
import pytz
import random
import string
import requests
from pytz import timezone
from datetime import datetime

from ..models.db import db
from flask import current_app
from requests import ConnectionError
from ..talent_config_manager import TalentConfigKeys
from ..models.user import User, UserScopedRoles, DomainRole
from ..error_handling import UnauthorizedError, ResourceNotFound, InvalidUsage, InternalServerError


JSON_CONTENT_TYPE_HEADER = {'content-type': 'application/json'}


def random_word(length):
    # Creates a random lowercase string, useful for testing data.
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def random_letter_digit_string(size=6, chars=string.lowercase + string.digits):
    # Creates a random string of lowercase/uppercase letter and digits. Useful for Oauth2 tokens.
    return ''.join(random.choice(chars) for _ in range(size))


def add_role_to_test_user(test_user, role_names):
    """
    This function will add roles to a test_user just for testing purpose
    :param User test_user: User object
    :param list[str] role_names: List of role names
    :return:
    """
    for role_name in role_names:
        try:
            DomainRole.save(role_name)
        except Exception:
            db.session.rollback()
            pass

    UserScopedRoles.add_roles(test_user, role_names)


def camel_case_to_snake_case(name):
    """ Convert camel case to underscore case
        socialNetworkId --> social_network_id

            :Example:

                result = camel_case_to_snake_case('socialNetworkId')
                assert result == 'social_network_id'

    """
    # name_ = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # return re.sub('([a-z0-9])([A-Z0-9])', r'\1_\2', name_).lower()
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('(.)([0-9]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def snake_case_to_pascal_case(name):
    """ Convert string or unicode from lower-case underscore to camel-case
        e.g. appt_type_id --> ApptTypeId

            :Example:

                result = snake_case_to_camel_case('social_network_id')
                assert result == 'SocialNetworkId'
    """
    if not isinstance(name, basestring):
        raise InvalidUsage('Include name as str.')
    splitted_string = name.split('_')
    # use string's class to work on the string to keep its type
    class_ = name.__class__
    return class_.join('', map(class_.capitalize, splitted_string))


def url_conversion(long_url):
    """
    We use Google's URL Shortener API to shorten the given URL.
    In this function we pass a URL which we want to shorten and on
    success it saves record in database and returns its id.
    :param long_url: The URL which we want to be shortened
    :type long_url: str
    :return: shortened URL, and error message if any else ''
    :rtype: tuple
    """
    if not isinstance(long_url, basestring):
        raise InvalidUsage('Pass URL(to be shortened) as a string',
                           error_code=InvalidUsage.http_status_code())
    google_api_url = 'https://www.googleapis.com/urlshortener/v1/url?key=%s'
    payload = json.dumps({'longUrl': long_url})
    response = http_request('POST',
                            google_api_url % current_app.config['GOOGLE_URL_SHORTENER_API_KEY'],
                            headers=JSON_CONTENT_TYPE_HEADER, data=payload)
    json_data = response.json()
    if 'error' not in json_data:
        return json_data['id'], ''
    else:
        error_message = "Error while shortening URL. Long URL is %s. " \
                        "Error dict is %s" % (long_url, json_data['error']['errors'][0])
        return None, error_message


def to_utc_str(dt):
    """
    This converts given datetime in '2015-10-08T06:16:55Z' format.
    :param dt: given datetime
    :type dt: datetime
    :return: UTC date in str
    :rtype: str
    """
    if not isinstance(dt, datetime):
        raise InvalidUsage('Given param should be datetime obj')
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_utc_datetime(dt, tz):
    """
    This method takes datetime object and timezone name and returns UTC specific datetime
    :Example:
        >> now = datetime.now()  # datetime(2015, 10, 8, 11, 16, 55, 520914)
        >> timezone = 'Asia/Karachi'
        >> utc_datetime = get_utc_datetime(now, timezone) # '2015-10-08T06:16:55Z
    :param dt: datetime object
    :type dt: datetime
    :return: timezone specific datetime object
    :rtype string
    """
    assert tz, 'Timezone should not be none'
    assert isinstance(dt, datetime), 'dt should be datetime object'
    # get timezone info from given datetime object
    local_timezone = timezone(tz)
    try:
        local_dt = local_timezone.localize(dt, is_dst=None)
    except ValueError:
        # datetime object already contains timezone info
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def http_request(method_type, url, params=None, headers=None, data=None, user_id=None):
    """
    This is common function to make HTTP Requests. It takes method_type (GET or POST)
    and makes call on given URL. It also handles/logs exception.
    :param method_type: GET or POST.
    :param url: resource URL.
    :param params: params to be sent in URL.
    :param headers: headers for Authorization.
    :param data: data to be sent.
    :param user_id: Id of logged in user.
    :type method_type: str
    :type url: str
    :type params: dict
    :type headers: dict
    :type data: dict
    :type user_id: int | long
    :return: response from HTTP request or None
    :Example:
        If we are requesting scheduler_service to GET a task, we will use this method as
            http_request('GET', SchedulerApiUrl.TASK % scheduler_task_id, headers=oauth_header)
    """
    logger = current_app.config[TalentConfigKeys.LOGGER]
    if not isinstance(method_type, basestring):
        raise InvalidUsage('Method type should be str. e.g. POST etc')
    if not isinstance(url, basestring):
        error_message = 'URL must be string. Unable to make "%s" Call' % method_type
        logger.error('http_request: Error: %s, user_id: %s'
                     % (error_message, user_id))
        raise InvalidUsage(error_message)
    if method_type.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
        method = getattr(requests, method_type.lower())
        response = None
        error_message = None
        try:
            response = method(url, params=params, headers=headers, data=data, verify=False)
            # If we made a bad request (a 4XX client error or 5XX server
            # error response),
            # we can raise it with Response.raise_for_status():"""
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == ResourceNotFound.http_status_code():
                # 404 is the error code for Resource Not found
                raise ResourceNotFound(response.content)
            elif e.response.status_code == UnauthorizedError.http_status_code():
                # 401 is the error code for Not Authorized user(Expired Token)
                raise UnauthorizedError(response.content)
            # checks if error occurred on "Server" or is it a bad request
            elif e.response.status_code < InternalServerError.http_status_code():
                try:
                    # In case of Meetup, we have error details in e.response.json()['errors'].
                    # So, tyring to log as much
                    # details of error as we can.
                    json_response = e.response.json()
                    if 'errors' in json_response:
                        error_message = \
                            e.message + ', Details: ' + json.dumps(json_response['errors'])
                    elif 'error_description' in json_response:
                        error_message = e.message + ', Details: ' + json.dumps(
                            json_response['error_description'])
                    else:
                        error_message = e.message
                except AttributeError:
                    error_message = e.message
            else:
                # raise any Server error
                raise
        except ConnectionError:
            # This check is for if any talent service is not running. It logs the URL on
            # which request was made.
            logger.exception(
                "http_request: Couldn't make %s call on %s. "
                "Make sure requested server is running." % (method_type, url))
            raise
        except requests.RequestException as e:
            logger.exception('http_request: HTTP request failed, %s' % e.message)
            raise

        if error_message:
            logger.exception('http_request: HTTP request failed, %s, '
                             'user_id: %s', error_message, user_id)
        return response
    else:
        logger.error('http_request: Unknown Method type %s ' % method_type)
        raise InvalidUsage('Unknown method type(%s) provided' % method_type)


def validate_required_fields(data_dict, required_fields):
    """
    This function returns the keys as specified by required_fields, that are not present in
    the data_dict. If any of the field is missing, it raises missing
    :param data_dict:
    :param required_fields:
    :type data_dict: dict
    :type required_fields: list
    :exception: Invalid Usage
    """
    if not isinstance(data_dict, dict):
        raise InvalidUsage('data_dict must be instance of dictionary.')
    if not isinstance(required_fields, (tuple, list)):
        raise InvalidUsage('required_fields must be instance of list.')
    missing_keys = list(set(required_fields) - set(data_dict.keys()))
    if missing_keys:
        raise InvalidUsage('Required fields are missing from given data.%s' % missing_keys,
                           error_code=InvalidUsage.http_status_code())


def find_missing_items(data_dict, required_fields=None, verify_all=False):
    """
    This function is used to find the missing items (either key or its value)in given
    data_dict. If verify_all is true, this function checks all the keys present in data_dict
    if they are empty or not. Otherwise it verify only those fields as given in required_fields.

    :Example:

        >>> data_dict = {'name' : 'Name', 'title': 'myTitle'}
        >>> missing_items = find_missing_items(data_dict, required_fields =['name', 'title', 'type']
        >>> print missing_items

         Output will be ['type']
    :param data_dict: given dictionary to be examined
    :param required_fields: keys which need to be checked
    :param verify_all: indicator if we want to check values of all keys or only keys
                            present in required_fields
    :type data_dict: dict
    :type required_fields: list | None
    :type verify_all: bool
    :return: list of missing items
    :rtype: list
    """
    if not isinstance(data_dict, dict):
        raise InvalidUsage('include data_dict as dict.')
    if not data_dict:  # If data_dict is empty, return all the required_fields as missing_item
        return [{item: ''} for item in required_fields]
    elif verify_all:
        # verify that all keys in the data_dict have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if not value and not value == 0]
    else:
        # verify if required fields are present as keys in data_dict
        validate_required_fields(data_dict, required_fields)
        # verify that keys of data_dict present in required_field have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if key in required_fields and not value and not value == 0]
    return [missing_item for missing_item in missing_items]


def raise_if_not_instance_of(obj, instances, exception=InvalidUsage):
    """
    This validates that given object is an instance of given instance. If it is not, it raises
    the given exception.
    :param obj: obj e,g. User object
    :param instances: Class for which given object is expected to be an instance.
    :param exception: Exception to be raised
    :type obj: object
    :type instances: class
    :type exception: Exception
    :exception: Invalid Usage
    """
    if not isinstance(obj, instances):
        given_obj_name = dict(obj=obj).keys()[0]
        error_message = '%s must be an instance of %s.' % (given_obj_name, '%s')
        if isinstance(instances, (list, tuple)):
            raise exception(error_message % ", ".join([instance.__name__
                                                       for instance in instances]))
        else:
            raise exception(error_message % instances.__name__)


def sample_phone_number():
    """Create random phone number.
    Phone number only creates area code + 7 random digits
    :rtype: str
    """
    first = random.randint(1, 9)
    second = random.randint(0, 99)
    area_code = (first * 100) + second
    middle = random.randint(101, 999)
    last_four = ''.join(map(str, random.sample(range(10), 4)))
    return "{}-{}-{}".format(area_code, middle, last_four)
