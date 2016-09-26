"""Misc functions that have no logical grouping to a module."""

__author__ = 'erikfarmer'

# Standard Imports
import re
import json
import random
import string

# Third Party
import requests
from flask import Flask
from itertools import izip_longest
from requests import ConnectionError
from flask import current_app, request
from werkzeug.exceptions import BadRequest
from contracts import contract

# Application Specific
from ..models.user import User
from ..talent_config_manager import TalentConfigKeys
from ..utils.validators import raise_if_not_positive_int_or_long
from ..error_handling import (UnauthorizedError, ResourceNotFound,
                              InvalidUsage, InternalServerError)
from ..custom_contracts import define_custom_contracts


define_custom_contracts()


JSON_CONTENT_TYPE_HEADER = {'content-type': 'application/json'}


class HttpMethods(object):
    """
    Here we have names of HTTP methods
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


def random_word(length):
    """Creates a random lowercase string, useful for testing data."""
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def random_letter_digit_string(size=6, chars=string.lowercase + string.digits):
    """Creates a random string of lowercase/uppercase letter and digits."""
    return ''.join(random.choice(chars) for _ in range(size))


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


def log_exception(message, app=None):
    """
    Log exception using logger with or without app_context
    :param message:
    :param app:
    :return:
    """
    if not app:
        logger = current_app.config[TalentConfigKeys.LOGGER]
        logger.exception(message)
        return

    assert isinstance(app, Flask), "app instance should be flask"

    logger = app.config[TalentConfigKeys.LOGGER]
    with app.app_context():
        logger.exception(message)


def log_error(message, app=None):
    """
    Log error using logger with or without app_context
    :param message:
    :param app:
    :return:
    """
    if not app:
        logger = current_app.config[TalentConfigKeys.LOGGER]
        logger.error(message)
        return

    assert isinstance(app, Flask), "app instance should be flask"

    logger = app.config[TalentConfigKeys.LOGGER]
    with app.app_context():
        logger.error(message)


def http_request(method_type, url, params=None, headers=None, data=None, user_id=None, app=None):
    """
    This is common function to make HTTP Requests. It takes method_type (GET or POST)
    and makes call on given URL. It also handles/logs exception.
    :param method_type: GET or POST.
    :param url: resource URL.
    :param params: params to be sent in URL.
    :param headers: headers for Authorization.
    :param data: data to be sent.
    :param user_id: Id of logged in user.
    :param app: flask app object if wanted to use this method using app_context()
    :type method_type: str
    :type url: str
    :type params: dict | None
    :type headers: dict | None
    :type data: dict | None
    :type user_id: int | long | None
    :return: response from HTTP request or None
    :Example:
        If we are requesting scheduler_service to GET a task, we will use this method as
            http_request('GET', SchedulerApiUrl.TASK % scheduler_task_id, headers=oauth_header)
    """

    if app and not isinstance(app, Flask):
        raise InternalServerError(error_message="app instance should be flask")

    if not isinstance(method_type, basestring):
        raise InternalServerError('Method type should be str. arg given: %s' % method_type)
    if not isinstance(url, basestring):
        error_message = 'URL must be string. Unable to make "%s" Call' % method_type
        log_error('http_request: Error: %s, user_id: %s, URL: %s, Headers: %s, Data: %s'
                  % (error_message, user_id, url, headers, data), app=app)
        raise InternalServerError(error_message)
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
                raise ResourceNotFound(str(e.response.json()))
            elif e.response.status_code == UnauthorizedError.http_status_code():
                # 401 is the error code for Not Authorized user(Expired Token)
                raise UnauthorizedError(str(e.response.json()))
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
                log_exception('''http_request: Server error, make sure requested server is running.
                                 URL:     %s
                                 Method:  %s
                                 Data:    %s
                                 Headers: %s''' % (url, method_type, data, headers))
                raise
        except ConnectionError:
            # This check is for if any talent service is not running. It logs the URL on
            # which request was made.
            log_exception(
                            "http_request: Couldn't make %s call on %s. "
                            "Make sure requested server is running. Headers: %s, Data: %s" % (method_type, url, headers,
                                                                                              data), app=app)
            raise
        except requests.Timeout as e:
            log_exception('http_request: HTTP request timeout, %s. URL: %s, Headers: %s, Data: %s' %
                          (e.message, url, headers, data))
            raise
        except requests.RequestException as e:
            log_exception('http_request: HTTP request failed, %s. URL: %s, Headers: %s, Data: %s,'
                          'Response: %s' % (e.message, url, headers, data, e.response))
            raise
        if error_message:
            log_exception('http_request: HTTP request failed, %s, '
                          'user_id: %s, URL: %s, Headers: %s, Data: %s' % (error_message, user_id, url,
                                                                           headers, data), app=app)
        return response
    else:
        log_error('http_request: Unknown Method type %s. URL: %s, Headers: %s, Data: %s' % (method_type, url, headers,
                                                                                           data), app=app)
        raise InternalServerError('Unknown method type(%s) provided. URL: %s, Headers: %s, Data: %s' %
                                  (method_type, url,
                                   headers, data))


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
    check_value = lambda value: not str(value).strip() and not value == 0
    if not data_dict:  # If data_dict is empty, return all the required_fields as missing_item
        return [{item: ''} for item in required_fields]
    elif verify_all:
        # verify that all keys in the data_dict have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems() if check_value(value)]
    else:
        # verify if required fields are present as keys in data_dict
        validate_required_fields(data_dict, required_fields)
        # verify that keys of data_dict present in required_field have valid values
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if key in required_fields and check_value(value)]
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
    :param (int | long | None) user_id: Id of user.
    :rtype: dict
    """
    if user_id:
        raise_if_not_positive_int_or_long(user_id)
    secret_key_id, jw_token = User.generate_jw_token(
        user_id=request.user.id if hasattr(request, 'user') else user_id)
    headers = {'Authorization': jw_token, 'X-Talent-Secret-Key-ID': secret_key_id}
    if content_type:
        headers['Content-Type'] = content_type
    return headers


def create_oauth_headers(oauth_token=None, user_id=None):
    """
    This function will return dict of Authorization and Content-Type headers. If the request context does not
    contain an access token, a dict of JWT based on the user ID and X-Talent-Secret-Key-ID headers are generated.
    :param oauth_token: Token for authentication.
    :param user_id: Id of user in case we are calling this function out od request context such as through celery.
    :type oauth_token: str | unicode | None
    :type user_id: int | long | None
    """
    oauth_token = oauth_token if oauth_token else request.oauth_token if hasattr(request, 'oauth_token') else None
    if user_id:
        raise_if_not_positive_int_or_long(user_id)
    if not oauth_token:
        return generate_jwt_headers(JSON_CONTENT_TYPE_HEADER['content-type'], user_id)
    else:
        authorization_header_value = oauth_token if 'Bearer' in oauth_token else 'Bearer %s' % oauth_token
        return {'Authorization': authorization_header_value, 'Content-Type': 'application/json'}


def validate_json_header(request):
    """
    Proper header should be {'content-type': 'application/json'} for POSTing
    some data on SMS campaign API.
    If header of request is not proper, it raises InvalidUsage exception
    :return:
    """
    if JSON_CONTENT_TYPE_HEADER['content-type'] not in request.content_type:
        raise InvalidUsage('Invalid header provided. Kindly send request with JSON data '
                           'and application/json content-type header')


def get_valid_json_data(req):
    """
    This first verifies that request has proper JSON content-type header
    and raise invalid usage error in case it doesn't has. From given request,
    we try to get data. We raise invalid usage exception if data is
    1) not JSON serializable
    2) not in dict format
    3) empty
    :param req:
    :return:
    """
    validate_json_header(req)
    try:
        data = req.get_json()
    except BadRequest:
        raise InvalidUsage('Given data is not JSON serializable.')
    if not isinstance(data, dict):
        raise InvalidUsage('Invalid POST data. Kindly send valid JSON data.')
    if not data:
        raise InvalidUsage('No data provided.')
    return data


def define_and_send_request(access_token, request, url, data=None):
    """
    Function will define request based on params and make the appropriate call.
    :param request_method:  can only be GET, POST, PUT, PATCH, or DELETE
    :param url: url for request
    :param access_token: token for authentication
    :param data: data in form of dictionary
    """
    request = request.lower()
    assert request in ['get', 'post', 'put', 'patch', 'delete']
    method = getattr(requests, request)
    if data is None:
        return method(url=url, headers={'Authorization': 'Bearer %s' % access_token})
    else:
        return method(url=url,
                      headers={'Authorization': 'Bearer %s' % access_token,
                               'content-type': 'application/json'},
                      data=json.dumps(data))


def purge_dict(dictionary, strip=True, keep_false=True, remove_empty_strings_only=False):
    """
    Function will "remove" dict's keys with empty values
    :param strip: if True, it will strip each value
    :type strip: bool
    :param keep_false: if keep_false is True, keys with values equaling 0 or False will not be removed
    :type keep_false: bool
    :param remove_empty_strings_only: if True, keys with None values will not be removed
    :type remove_empty_strings_only: bool
    :type dictionary:  dict
    :rtype:  dict
    """

    def clean(value):
        return value.strip() if isinstance(value, basestring) else value

    # strip all values & return all keys except keys with empty-string values
    if remove_empty_strings_only:
        return {k: clean(v) for k, v in dictionary.items() if clean(v) != ''}

    # strip all values & return keys with values that aren't None
    elif strip and not remove_empty_strings_only and not keep_false:
        return {k: clean(v) for k, v in dictionary.items() if v is not None}

    # removes keys with None and empty string values
    elif strip and keep_false:
        for k, v in dictionary.items():
            cleaned_value = clean(v)
            if cleaned_value is None or cleaned_value == '':
                del dictionary[k]
        return dictionary

    # strip key-values and keep keys with truthy values
    elif strip and not keep_false:
        return {k: clean(v) for k, v in dictionary.items() if (v or clean(v))}

    # keep keys with truthy values, but doesn't strip values
    else:
        return {k: v for k, v in dictionary.items() if (v or clean(v))}


def normalize_value(value):
    """
    Function will strip & lower value
    Value must be string, not None
    :param value: any string value
    :type value: str
    :rtype:  str
    """
    assert isinstance(value, basestring), "value must be of type string"
    return value.strip().lower()


@contract
def send_request(method, url, access_token, data=None, params=None, is_json=True, verify=True):
    """
    This is a generic method to send HTTP request. We can just pass our data/ payload
    and it will make it json and send it to target url with application/json as content-type
    header.
    :param http_method method: standard HTTP method like post, get (in lowercase)
    :param string url: target url
    :param (string | None)  access_token: authentication token, token can be empty, None or invalid
    :param (dict | None) data: payload data for request
    :param (dict | None) params: query params
    :param bool is_json: a flag to determine, whether we need to dump given data or not.
            default value is true because most of the APIs are using json content-type.
    :param bool verify: set this to false
    :return: request method i.e POST, GET, DELETE, PATCH
    :rtype: Response
    """
    method = method.lower()
    request_method = getattr(requests, method)
    if access_token:
        headers = dict(Authorization=access_token if 'Bearer' in access_token else 'Bearer %s' % access_token)
    else:
        headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, params=params, headers=headers, verify=verify)
