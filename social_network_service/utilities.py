"""
This file contains some (supposedly) common utility functions that may be used
or consumed by various programs.
"""
import re
import imp
import sys
import requests
import importlib
import json
import logging
import datetime
from requests_oauthlib import OAuth2Session

from gt_common.models.user import User
from gt_common.models.social_network import SocialNetwork
from social_network_service.custom_exections import SocialNetworkNotImplemented, ApiException

logger = logging.getLogger('event_service.app')
OAUTH_SERVER = 'http://127.0.0.1:8081/oauth2/authorize'


class Attendee(object):
    """
    Basically a placeholder object that will be used while processing
    RSVPs. See base.py
    """

    def __init__(self, *args, **kwargs):
        self.first_name = None  # first name of attendee
        self.last_name = None  # last name of attendee
        self.full_name = None  # full name of attendee
        self.profile_url = None  # profile url of attendee
        self.picture_url = None  # picture url of attendee
        self.city = None  # city of attendee
        self.country = None  # country of attendee
        self.latitude = None  # latitude of attendee's location
        self.longitude = None  # longitude of attendee's location
        self.zip = None  # zip code of attendee's city/location
        self.rsvp_id = None  # attendee's rsvp id in db
        self.email = None  # attendee's email address
        self.rsvp_status = None  # attendee's rsvp status
        self.candidate_id = None  # attendee's id in candidate table
        self.event = None  # attendee's corresponding event in database
        self.vendor_img_link = None  # attendee's vendor image link
        # (image is present in static files of gt-app)
        self.added_time = None  # attendee's time of rsvp
        self.gt_user_id = None  # attendee's corresponding gt-user id
        self.vendor_rsvp_id = None  # attendee's vendor rsvp id
        self.social_network_id = None  # attendee's social network id
        self.candidate_event_rsvp_id = None  # attendee's entry id in
        self.candidate_source_id = None  # attendee's candidate_source id
        # from db
        self.source_product_id = None  # attendee's source product id in database
        # candidate_event_rsvp

    def __str__(self):
        return 'Name: %s, RSVP_ID: %s, EMAIL: %s' % (self.full_name,
                                                     self.rsvp_id,
                                                     self.email)


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def milliseconds_since_epoch(dt):
    assert isinstance(dt, datetime.datetime) == True
    return unix_time(dt) * 1000.0


def milliseconds_since_epoch_to_dt(epoch):
    return datetime.datetime.fromtimestamp(epoch / 1000.0)


def authenticate_user(request):
    """
    :rtype: gluon.dal.objects.Row | None
    """
    auth_token = request.headers.get('Authorization')
    if auth_token and isinstance(auth_token, basestring):
        auth_token = auth_token.lower().replace('bearer ', '')
        try:
            remote = OAuth2Session(token={'access_token': auth_token})
            response = remote.get(OAUTH_SERVER)
            if response.status_code == 200:
                user_id = response.json().get('user_id') or ''
                return User.get_by_id(user_id) if user_id else None
            else:
                return None
        except Exception as e:
            return None
    else:
        return None


def get_message_to_log(gt_user='', function_name='', error='', class_name='', file_name=''):
    """
    Here we define descriptive message to be used for logging purposes
    :param function_name:
    :param error:
    :param class_name:
    :return:
    """
    message_to_log = {
        'user': gt_user,
        'class': class_name,
        'fileName': file_name,
        'functionName': function_name,
        'error': error}
    return message_to_log


def log_exception(message_dict):
    """
    This function logs exception when it is called inside a catch block
    where ever it is called using message_dict as descriptive message to log.
    :param message_dict:
    :return:
    """
    message_to_log = ("Reason: %(error)s \n"
                      "functionName: %(functionName)s, "
                      "fileName: %(fileName)s, "
                      "User: %(user)s" % message_dict)
    if message_dict.get('class'):
        message_to_log += ", class: %(class)s" % message_dict
    logger.exception(message_to_log)


def log_error(message_dict):
    """
    This function logs error using message_dict as descriptive message to log.
    :param message_dict:
    :return:
    """
    message_to_log = ("Reason: %(error)s \n"
                      "functionName: %(functionName)s, "
                      "fileName: %(fileName)s, "
                      "User: %(user)s" % message_dict)
    if message_dict.get('class'):
        message_to_log += ", class: %(class)s" % message_dict
    logger.error(message_to_log)


def http_request(method_type, url, params=None, headers=None, data=None, message_to_log=None):
    """
    This is common function to make HTTP Requests. It takes method_type (GET or POST)
    and makes call on given URL. It also handles/logs exception.
    :param method_type: GET or POST.
    :param url: resource URL.
    :param params: params to be sent in URL.
    :param headers: headers for Authorization.
    :param data: data to be sent.
    :param message_to_log: descriptive message to log when exception occurs.
    :return:
    """
    if method_type in ['GET', 'POST']:
        method = getattr(requests, method_type.lower())
        error_message = None
        if url:
            try:
                response = method(url, params=params, headers=headers, data=data)
                # If we made a bad request (a 4XX client error or 5XX server error response),
                # we can raise it with Response.raise_for_status():"""
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if 'errors' in e.response.json():
                    error_message = e.message + ' , Details: ' \
                                    + json.dumps(e.response.json().get('errors'))
                else:
                    error_message = e.message
            except requests.RequestException as e:
                error_message = e.message
            if error_message and message_to_log:
                message_to_log.update({'error': error_message})
                log_exception(message_to_log)
            return response
        else:
            error_message = 'URL is None. Unable to make %s Call' % method_type
            logger.error(error_message)
    else:
        logger.error('Unknown Method type %s ' % method_type)


def get_class(social_network_name, category):
    """
    Here we pass following parameters
    :param social_network_name:
    :param category:
    and we import the required class and return it
    :return:
    """
    function_name = 'get_class()'
    message_to_log = get_message_to_log(function_name=function_name,
                                        file_name=__file__)
    if category == 'social_network':
        module_name = 'social_network_service.' + social_network_name
    else:
        module_name = 'social_network_service.' + category + '.' + social_network_name.lower()
    try:
        module = importlib.import_module(module_name)
        _class = getattr(module, social_network_name.title())
    except ImportError as e:
        error_message = 'Social Network "%s" is not allowed for now, ' \
                        'please implement code for this social network.' \
                        % social_network_name
        message_to_log.update({'error': error_message})
        log_error(message_to_log)
        raise SocialNetworkNotImplemented('Import Error: Unable to import module for required social network')
    except AttributeError:
        raise ApiException('APIError: Unable to import module for required social network', status_code=500)
    return _class


def camel_case_to_snake_case(name):
    """ Convert camel case to underscore case
        e.g. apptTypeId --> appt_type_id
    """
    name_ = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name_).lower()


def camel_case_to_title_case(name):
    """ Converts camel case to title case
        e.g. apptTypeId --> Appt Type I
    """
    name_ = camel_case_to_snake_case(name)
    return ' '.join(name_.split('_')).title()


def snake_case_to_camel_case(name):
    """ Convert string or unicode from lower-case underscore to camel-case
        e.g. appt_type_id --> apptTypeId
    """
    splitted_string = name.split('_')
    # use string's class to work on the string to keep its type
    class_ = name.__class__
    return splitted_string[0] + class_.join('', map(class_.capitalize, splitted_string[1:]))


def convert_keys_to_camel_case(dictionary):
    """
    Convert a dictionary keys to camel case
    e.g.
    data = {'event_title': 'Test event',
            'event_description': 'Test event description'
            'event_start_datetime': '2015-12-12 12:00:00'
            }
    to

    data = {'eventTitle': 'Test event',
            'eventDescription': 'Test event description'
            'eventStartDatetime': '2015-12-12 12:00:00'
            }

    """
    data = {}
    for key, val in dictionary.items():
        data[snake_case_to_camel_case(str(key))] = val
    return data


def convert_keys_to_snake_case(dictionary):
    """
    Convert a dictionary keys to snake case
    e.g.

    data = {'eventTitle': 'Test event',
            'eventDescription': 'Test event description'
            'eventStartDatetime': '2015-12-12 12:00:00'
            }

    to

    data = {'event_title': 'Test event',
            'event_description': 'Test event description'
            'event_start_datetime': '2015-12-12 12:00:00'
    }

    """
    data = {}
    for key, val in dictionary.items():
        data[camel_case_to_snake_case(str(key))] = val
    return data


def import_from_dist_packages(name, custom_name=None):
    """
    This function is used to import facebook-sdk module rather than local
    module named as facebook
    :param name:
    :param custom_name:
    :return:
    """
    paths_to_be_searched = []
    custom_name = custom_name or name
    for path in sys.path[1:]:
        if 'site-packages' in path:
            paths_to_be_searched.append(path)
    f, pathname, desc = imp.find_module(name, paths_to_be_searched)
    module = imp.load_module(custom_name, f, pathname, desc)
    f.close()
    return module


