"""Misc functions that have no logical grouping to a module."""
__author__ = 'erikfarmer'
import json
import requests
from flask import current_app, request
from requests.packages.urllib3.connection import ConnectionError
from ..talent_config_manager import TalentConfigKeys
from ..error_handling import UnauthorizedError, ResourceNotFound, InvalidUsage, InternalServerError
import re
import random
import string
from itertools import izip_longest
from ..models.db import db
from ..models.user import User, UserScopedRoles, DomainRole

JSON_CONTENT_TYPE_HEADER = {'content-type': 'application/json'}


def random_word(length):
    """Creates a random lowercase string, usefull for testing data."""
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def random_letter_digit_string(size=6, chars=string.lowercase + string.digits):
    """Creates a random string of lowercase/uppercase letter and digits."""
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


def grouper(iterable, group_size, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    i.e grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    :param iterable: Iterable item for 'chunking'.
    :param group_size: How many items should be in a group.
    :param fillvalue: Optional arg to fill chunks that are less than the defined group size.
    :return type: itertools.izip_longest
    """
    args = [iter(iterable)] * group_size
    return izip_longest(*args, fillvalue=fillvalue)


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
            http_request('GET', SchedulerApiUrl.TASK % scheduler_task_id, headers=auth_header)
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
                    if 'errors' in e.response.json():
                        error_message = e.message + ', Details: ' + json.dumps(
                            e.response.json().get('errors'))
                    elif 'error_description' in e.response.json():
                        error_message = e.message + ', Details: ' + json.dumps(
                            e.response.json().get('error_description'))
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


def generate_jwt_headers(content_type=None, user_id=None):
    """
    This function will return a dict of JWT based on the user ID and X-Talent-Secret-Key-ID and optional content-type
    :param str content_type: content-type header value
    :return:
    """
    secret_key_id, jw_token = User.generate_jw_token(user_id=request.user.id if request.user else user_id)
    headers = {'Authorization': jw_token, 'X-Talent-Secret-Key-ID': secret_key_id}
    if content_type:
        headers['Content-Type'] = content_type
    return headers


def create_oauth_headers():
    """
    This function will return dict of Authorization and Content-Type headers. If the request context does not
    contain an access token, a dict of JWT based on the user ID and X-Talent-Secret-Key-ID headers are generated.
    :return:
    """
    oauth_token = request.oauth_token
    if not oauth_token:
        return generate_jwt_headers('application/json')
    else:
        authorization_header_value = oauth_token if 'Bearer' in oauth_token else 'Bearer %s' % oauth_token
        return {'Authorization': authorization_header_value, 'Content-Type': 'application/json'}


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