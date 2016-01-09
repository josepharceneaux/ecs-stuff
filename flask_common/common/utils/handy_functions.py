import json

import requests
from flask import current_app

from scheduler_service import TalentConfigKeys
from ..error_handling import ForbiddenError, UnauthorizedError, ResourceNotFound

__author__ = 'erikfarmer'

import re
import random
import string
from ..models.user import User, UserScopedRoles, DomainRole


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
    """
    response = None
    logger = current_app.config[TalentConfigKeys.LOGGER]
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
                if e.response.status_code in [UnauthorizedError.http_status_code(), ResourceNotFound.http_status_code()]:
                    # 401 is the error code for Not Authorized user(Expired Token)
                    # 404 is the error code for Resource Not found
                    raise
                # checks if error occurred on "Server" or is it a bad request
                elif e.response.status_code < 500:
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
                    except Exception:
                        error_message = e.message
                else:
                    # raise any Server error
                    raise
            except requests.RequestException as e:
                if hasattr(e.message, 'args'):
                    if 'Connection aborted' in e.message.args[0]:
                        logger.exception(
                            "http_request: Couldn't make %s call on %s. "
                            "Make sure requested server is running." % (method_type, url))
                        raise ForbiddenError
                error_message = e.message
            if error_message:
                logger.exception('http_request: HTTP request failed, %s, '
                                 'user_id: %s', error_message, user_id)
            return response
        else:
            error_message = 'URL is None. Unable to make "%s" Call' % method_type
            logger.error('http_request: Error: %s, user_id: %s'
                                                              % (error_message, user_id))
    else:
        logger.error('Unknown Method type %s ' % method_type)