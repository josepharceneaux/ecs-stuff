"""Misc functions that have no logical grouping to a module."""
__author__ = 'erikfarmer'
import json
import requests
from flask import current_app
from requests.packages.urllib3.connection import ConnectionError
from ..talent_config_manager import TalentConfigKeys
from ..error_handling import UnauthorizedError, ResourceNotFound, InvalidUsage, InternalServerError
import re
import random
import string
from itertools import izip_longest
from ..models.db import db
from ..models.user import User, UserScopedRoles, DomainRole


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
    logger = app.config[TalentConfigKeys.LOGGER]
    if app:
        with app.app_context():
            logger.exception(message)
    else:
        logger.exception(message)


def log_error(message, app=None):
    """
    Log error using logger with or without app_context
    :param message:
    :param app:
    :return:
    """
    logger = app.config[TalentConfigKeys.LOGGER]
    if app:
        with app.app_context():
            logger.error(message)
    else:
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
    :type params: dict
    :type headers: dict
    :type data: dict
    :type user_id: int | long
    :return: response from HTTP request or None
    :Example:
        If we are requesting scheduler_service to GET a task, we will use this method as
            http_request('GET', SchedulerApiUrl.TASK % scheduler_task_id, headers=auth_header)
    """
    if not isinstance(method_type, basestring):
        raise InvalidUsage('Method type should be str. e.g. POST etc')
    if not isinstance(url, basestring):
        error_message = 'URL must be string. Unable to make "%s" Call' % method_type
        log_error('http_request: Error: %s, user_id: %s'
                  % (error_message, user_id), app=app)
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
            log_exception(
                            "http_request: Couldn't make %s call on %s. "
                            "Make sure requested server is running." % (method_type, url), app=app)
            raise
        except requests.RequestException as e:
            log_exception('http_request: HTTP request failed, %s' % e.message)
            raise

        if error_message:
            log_exception('http_request: HTTP request failed, %s, '
                                                   'user_id: %s' % (error_message, user_id), app=app)
        return response
    else:
        log_error('http_request: Unknown Method type %s ' % method_type, app=app)
        raise InvalidUsage('Unknown method type(%s) provided' % method_type)


def get_valid_json_data(req):
    data = req.get_json()
    if data is None:
        raise InvalidUsage('Kindly send request with JSON data and '
                           'application/json content-type header')
    if not isinstance(data, dict):
        raise InvalidUsage('Invalid POST data. Kindly send valid JSON data')
    if not len(data):
        raise InvalidUsage('Request data is empty')
    return data


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
