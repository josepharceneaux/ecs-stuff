__author__ = 'erikfarmer'
import re
import json
import pytz
import random
import string
import requests
from pytz import timezone
from datetime import datetime

from flask import current_app
from ..routes import AuthApiUrl
from ..talent_config_manager import TalentConfigKeys
from requests.packages.urllib3.connection import ConnectionError
from ..error_handling import UnauthorizedError, ResourceNotFound, InvalidUsage, InternalServerError
from ..models.user import User, UserScopedRoles, DomainRole
from sqlalchemy.sql.expression import ClauseElement
from werkzeug.security import generate_password_hash

JSON_CONTENT_TYPE_HEADER = {'content-type': 'application/json'}


def random_word(length):
    # Creates a random lowercase string, useful for testing data.
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


def find_missing_items(data_dict, required_fields=None, verify_values_of_all_keys=False):
    """
    This function is used to find the missing items in given data_dict. If verify_all
    is true, this function checks all the keys present in data_dict if they are empty or not.
    Otherwise it verify only those fields as given in required_fields.
    :param data_dict: given dictionary to be examined
    :param required_fields: keys which need to be checked
    :param verify_values_of_all_keys: indicator if we want to check values of all keys or only keys
                            present in required_fields
    :type data_dict: dict
    :type required_fields: list | None
    :type verify_values_of_all_keys: bool
    :return: list of missing items
    :rtype: list
    """
    if not data_dict:  # If data_dict is empty, return all the required_fields as missing_item
        return [{item: ''} for item in required_fields]
    elif verify_values_of_all_keys:
        # Check if required keys are present
        missing_keys = get_missing_keys(data_dict)
        if missing_keys:
            raise InvalidUsage('Required fields are missing from given data.%s' % missing_keys,
                               error_code=InvalidUsage.http_status_code())
        # verify that all keys in the data_dict have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if not value and not value == 0]
    else:
        missing_keys = get_missing_keys(data_dict, required_fields=required_fields)
        if missing_keys:
            raise InvalidUsage('Required fields are missing from given data. %s' % missing_keys,
                               error_code=InvalidUsage.http_status_code())
        # verify that keys of data_dict present in required_field have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if key in required_fields and not value and not value == 0]
    return [missing_item for missing_item in missing_items]


def get_missing_keys(data_dict, required_fields=None):
    """
    This function returns the keys that are not present in the data_dict.
    If required_fields is provided, it only checks for those keys otherwise it checks all
    the keys of data_dict.
    :param data_dict:
    :param required_fields:
    :type data_dict: dict
    :type required_fields: list | None
    :return:
    """
    missing_keys = filter(lambda required_key: required_key not in data_dict,
                          required_fields if required_fields else data_dict.keys())
    return missing_keys

def create_test_user(session, domain_id, password):
    random_email = ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
    email = '%s.sample@example.com' % random_email
    first_name = 'John'
    last_name = 'Sample'
    test_user = User(
        email=email,
        password=generate_password_hash(password, method='pbkdf2:sha512'),
        domain_id=domain_id,
        first_name=first_name,
        last_name=last_name,
        expiration=None
    )
    session.add(test_user)
    session.commit()
    return test_user


def get_access_token(user, password, client_id, client_secret):
    params = dict(grant_type="password", username=user.email, password=password)
    auth_service_token_response = requests.post(AuthApiUrl.TOKEN_CREATE,
                                                params=params,
                                                auth=(client_id, client_secret)).json()
    if not (auth_service_token_response.get(u'access_token') and auth_service_token_response.get(
            u'refresh_token')):
        raise Exception("Either Access Token or Refresh Token is missing")
    else:
        return auth_service_token_response.get(u'access_token')


def add_role_to_test_user(test_user, role_names):
    """
    This function will add roles to a test_user just for testing purpose
    :param User test_user: User object
    :param list[str] role_names: List of role names
    :return:
    """
    for role_name in role_names:
        if not DomainRole.get_by_name(role_name):
            DomainRole.save(role_name)
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

    payload = json.dumps({'longUrl': long_url})
    response = http_request('POST', 'https://www.googleapis.com/urlshortener/v1/url?key='
                            + current_app.config['GOOGLE_URL_SHORTENER_API_KEY'],
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
    except ValueError as e:
        # datetime object already contains timezone info
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def random_letter_digit_string(size=6, chars=string.lowercase + string.digits):
    # Creates a random string of lowercase/uppercase letter and digits. Useful for Oauth2 tokens.
    return ''.join(random.choice(chars) for _ in range(size))


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
                except json.JSONDecoder:
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
