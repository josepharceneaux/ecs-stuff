"""
This file contains some (supposedly) common utility functions that may be used
or consumed by various programs.
"""
import re
import imp
import sys
import json
import logging
import inspect
import requests
import datetime
import traceback
import importlib


from requests_oauthlib import OAuth2Session

from common.models.user import User
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


def get_callee_data():
    current_frame = inspect.currentframe()
    callee_frame = inspect.getouterframes(current_frame, 2)
    length_of_frame = len(callee_frame)
    no_of_items = list(range(0, length_of_frame-1))
    no_of_item = None
    for item in no_of_items:
        if length_of_frame - item == 4:
            no_of_item = item
    if no_of_item:
        try:
            callee_data = {
                'file_name': callee_frame[no_of_item][1],
                'line_no': callee_frame[no_of_item][2],
                'class_name': callee_frame[no_of_item][0].f_locals['self'].__class__.__name__
                if hasattr(callee_frame[no_of_item][0].f_locals, 'self') else '',
                'function_name': callee_frame[no_of_item][3]}
        except Exception as e:
            callee_data = {'traceback_info': traceback.format_exc()}
        return callee_data


def log_error(user_id_and_error_message):
    """
    Here we do the descriptive logging. 'user_id_and_error_message' is passed
    in parameters which contains error details in 'error' and User Id in
    'user_id'. We first get the information of callee using get_callee_data(),
    and append user_id_and_error_message in it. Finally we log the descriptive
    error using logger.error().
    :param user_id_and_error_message:
    :return:
    """
    # get_callee_data() returns the dictionary of callee data
    callee_data_dict = get_callee_data()
    # appends user_id_and_error_message in callee_data_dict
    callee_data_dict.update(user_id_and_error_message)
    if get_callee_data().has_key('traceback_info'):
        callee_data = ("Reason: %(traceback_info)s \n"
                       "User Id: %(user_id)s" % callee_data_dict)
    else:
        callee_data = ("Reason: %(error)s"
                       "function Name: %(function_name)s, "
                       "file Name: %(file_name)s, "
                       "line No: %(line_no)s",
                       "User Id: %(user_id)s" % callee_data_dict)
        if callee_data_dict.get('class_name'):
            callee_data += ", class: %(class_name)s" % callee_data_dict
    logger.error(callee_data)


def log_exception(user_id_and_error_message):
    """
    Here we do the descriptive logging. 'user_id_and_error_message' is passed
    in parameters which contains exception details in 'error' and User Id in
    'user_id'. We first get the information of callee using get_callee_data(),
    and append user_id_and_error_message in it. Finally we log the descriptive
    error using logger.exception()
    :param user_id_and_error_message:
    :return:
    """
    # get_callee_data() returns the dictionary of callee data
    callee_data_dict = get_callee_data()
    # appends user_id_and_error_message in callee_data_dict
    callee_data_dict.update(user_id_and_error_message)
    if get_callee_data().has_key('traceback_info'):
        callee_data = ("Reason: %(traceback_info)s \n"
                       "User Id: %(user_id)s" % callee_data_dict)
    else:
        callee_data = ("Reason: %(error)s"
                       "function Name: %(function_name)s, "
                       "file Name: %(file_name)s, "
                       "line No: %(line_no)s",
                       "User Id: %(user_id)s" % callee_data_dict)
        if callee_data_dict.get('class_name'):
            callee_data += ", class: %(class_name)s" % callee_data_dict
    logger.exception(callee_data)


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
    :return:
    """
    response = None
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
            if error_message:
                log_exception({'user_id': user_id,
                               'error': error_message})
            return response
        else:
            error_message = 'URL is None. Unable to make %s Call' % method_type
            log_error({'user_id': user_id,
                       'error': error_message})
    else:
        logger.error('Unknown Method type %s ' % method_type)


def get_class(social_network_name, category, user_credentials=None):
    """
    This function is used to import module from given parameters.
    Here we pass following parameters
    :param social_network_name:
    :param category:
    and we import the required class and return it
    :return:
    """
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
        log_error({'user_id': user_credentials.user_id if user_credentials else '',
                   'error': error_message})
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

