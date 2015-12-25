import re
import json
import requests
import random
import string

from flask import current_app
from ..routes import AuthApiUrl
from ..models.user import User, UserScopedRoles
from sqlalchemy.sql.expression import ClauseElement
from werkzeug.security import generate_password_hash
from ..error_handling import ForbiddenError, InvalidUsage

GOOGLE_URL_SHORTENER_API_KEY = 'AIzaSyCT7Gg3zfB0yXaBXSPNVhFCZRJzu9WHo4o'
GOOGLE_URL_SHORTENER_API_URL = 'https://www.googleapis.com/urlshortener/v1/url?key=' \
                               + GOOGLE_URL_SHORTENER_API_KEY
JSON_CONTENT_TYPE_HEADER = {'content-type': 'application/json'}


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
    :return: response from HTTP request or None
    """
    response = None
    if method_type in ['GET', 'POST', 'PUT', 'DELETE']:
        method = getattr(requests, method_type.lower())
        error_message = None
        if url:
            try:
                response = method(url, params=params, headers=headers, data=data, verify=False)
                # If we made a bad request (a 4XX client error or 5XX server
                # error response),
                # we can raise it with Response.raise_for_status():"""
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [401]:
                    # 401 is the error code for Not Authorized user(Expired Token)
                    raise
                # checks if error occurred on "Server" or is it a bad request
                elif e.response.status_code < 500:
                    try:
                        # In case of Meetup, we have error details in e.response.json()['errors'].
                        # So, tyring to log as much
                        # details of error as we can.
                        if 'errors' in e.response.json():
                            error_message = e.message + ', Details: ' + json.dumps(e.response.json().get('errors'))
                        elif 'error_description' in e.response.json():
                            error_message = e.message + ', Details: ' + json.dumps(e.response.json().get('error_description'))
                        else:
                            error_message = e.message
                    except Exception:
                        error_message = e.message
                else:
                    # raise any Server error
                    raise
            except requests.RequestException as e:
                if hasattr(e.message, 'args'):
                    if 'Connection aborted' in e.message.args[0]:
                        current_app.logger.exception(
                            "http_request: Couldn't make %s call on %s. "
                            "Make sure requested server is running." % (method_type, url))
                        raise ForbiddenError
                error_message = e.message
            if error_message:
                current_app.logger.exception('http_request: HTTP request failed, %s, '
                                             'user_id: %s', error_message, user_id)
            return response
        else:
            error_message = 'URL is None. Unable to make "%s" Call' % method_type
            current_app.logger.error('http_request: Error: %s, user_id: %s'
                                     % (error_message, user_id))
    else:
        current_app.logger.error('Unknown Method type %s ' % method_type)


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
        # verify that all keys in the data_dict have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if not value and not value == 0]
    else:
        # verify that keys of data_dict present in required_field have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if key in required_fields and not value and not value == 0]
    return [missing_item for missing_item in missing_items]


def create_test_user(session, domain_id, password):
    random_email = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
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
    auth_service_token_response = requests.post(AuthApiUrl.TOKEN_URL,
                                                params=params, auth=(client_id, client_secret)).json()
    if not (auth_service_token_response.get(u'access_token') and auth_service_token_response.get(u'refresh_token')):
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


def url_conversion(long_url):
    """
    We use Google's URL Shortener API to shorten the given URL.
    In this function we pass a URL which we want to shorten and on
    success it saves record in database and returns its id.
    :param long_url: The URL which we want to be shortened
    :type long_url: str
    :param long_url:
    :return: shortened URL, and error message if any else ''
    :rtype: tuple
    """
    if not isinstance(long_url, basestring):
        raise InvalidUsage(error_message='Pass URL(to be shortened) as a string',
                           error_code=InvalidUsage.http_status_code())

    payload = json.dumps({'longUrl': long_url})
    response = http_request('POST', GOOGLE_URL_SHORTENER_API_URL,
                            headers=JSON_CONTENT_TYPE_HEADER, data=payload)
    json_data = response.json()
    if 'error' not in json_data:
        short_url = json_data['id']
        # long_url = json_data['longUrl']
        current_app.logger.info("url_conversion: Long URL was: %s" % long_url)
        current_app.logger.info("url_conversion: Shortened URL is: %s" % short_url)
        return short_url, ''
    else:
        error_message = "Error while shortening URL. Long URL is %s. " \
                        "Error dict is %s" % (long_url, json_data['error']['errors'][0])
        return None, error_message


def is_iso_8601_format(str_datetime):
    """
    This validates the given datetime is in ISO format or not. Proper format should be like
    '2015-10-08T06:16:55Z'.

    :param str_datetime: str
    :type str_datetime: str
    :return: True if given datetime is valid, False otherwise.
    :rtype: bool
    """
    utc_pattern = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
    return re.match(utc_pattern, str_datetime)


def is_valid_url_format(url):
    """
    Reference: https://github.com/django/django-old/blob/1.3.X/django/core/validators.py#L42
    """
    regex = re.compile(
        r'^(http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)