"""
This file contains some (supposedly) common utility functions that may be used
or consumed by various programs.
"""
import re
import imp
import sys
import json
import inspect
import pytz
import requests
import datetime
import traceback
import importlib

from requests_oauthlib import OAuth2Session

from social_network_service import logger
from social_network_service import flask_app as app
from social_network_service.custom_exections import SocialNetworkNotImplemented,\
    ApiException, AccessTokenHasExpired

from common.models.user import User


OAUTH_SERVER = app.config['OAUTH_SERVER_URI']


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
    selected_items = []
    for item in no_of_items:
        # ignoring standard library files of python and pycharm
        if 'site-packages' not in callee_frame[item][1] \
                and 'pycharm' not in callee_frame[item][1]:
            selected_items.append(item)
        else:
            break
    for item in selected_items:
        if len(selected_items) - item == 4:
            no_of_item = item
            break
    if no_of_item:
        try:
            callee_data = {
                'file_name': callee_frame[no_of_item][1],
                'line_no': callee_frame[no_of_item][2],
                'class_name': callee_frame[no_of_item][0].f_locals['self'].__class__.__name__
                if callee_frame[no_of_item][0].f_locals.has_key('self') else '',
                'function_name': callee_frame[no_of_item][3]}
        except:
            callee_data = {'traceback_info': traceback.format_exc()}
        return callee_data


def log_error(log_data):
    """
    :param log_data: is a dict which contains error details and User Id in
                    keys 'error' and 'user_id' respectively.

    - Here we do the descriptive logging.

    - We first get the information of callee using get_data_to_log()
        and then we log the error using logger.error()

    - callee contains the useful information of traceback like
        Reason of error, function name, file name, user id, class name etc.

    - This function is called usually inside try except block.

    :Example:

        log_error({'user_id': user_id,
                   'error': error_message})
    ** See Also:
        - Have a look on get_access_and_refresh_token() defined in
        social_network_service/base.py for more insight.

    :param log_data:
    :return:
    """
    callee_data = get_data_to_log(log_data)
    logger.error(callee_data)


def log_exception(log_data):
    """
    :param log_data: is a dict which contains error details and User Id in
                     keys 'error' and 'user_id' respectively.

    - Here we do the descriptive logging.

    - We first get the information of callee using get_data_to_log()
        and then we log the error using logger.exception()

    - callee contains the useful information of traceback like
        Reason of error, function name, file name, user id, class name etc.

    - This function is called usually inside try except block.

    :Example:

        log_exception({'user_id': user_id,
                       'error': error_message})
    ** See Also:
        - Have a look on get_access_and_refresh_token() defined in
        social_network_service/base.py for more insight.
    """
    callee_data = get_data_to_log(log_data)
    logger.exception(callee_data)


def get_data_to_log(log_data):
    """
    :param log_data:  is a dict which contains error details and User Id in
            keys 'error'  in 'user_id' respectively.

    - We first get the information of callee using get_callee_data(),
        and append user_id_and_error_message in it. Finally we return the
        descriptive error message.

    - This function is called from log_error() and log_exception() defined in
        social_network_service/utilities.py

    ** See Also:
        - Have a look on log_error() or log_exception() defined in
        social_network_service/utilities.py
    :return: callee_data which contains the useful information of traceback
            like Reason of error, function name, file name, user id etc.
    """
    # get_callee_data() returns the dictionary of callee data
    callee_data_dict = get_callee_data()
    # appends user_id_and_error_message in callee_data_dict
    callee_data_dict.update(log_data)
    if callee_data_dict.has_key('traceback_info'):
        callee_data = ("\nReason: %(traceback_info)s \n"
                       "User Id: %(user_id)s" % callee_data_dict)
    elif callee_data_dict.get('user_id'):
        callee_data = ("\nReason: %(error)s,\n"
                       "function Name: %(function_name)s,\n"
                       "file Name: %(file_name)s,\n"
                       "line No: %(line_no)s,\n"
                       "User Id: %(user_id)s" % callee_data_dict)
        if callee_data_dict.get('class_name'):
            callee_data += ",\nclass: %(class_name)s" % callee_data_dict
    else:
        callee_data = ("Reason: %(error)s"% callee_data_dict)
    return callee_data


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
    if method_type in ['GET', 'POST', 'PUT', 'DELETE']:
        method = getattr(requests, method_type.lower())
        error_message = None
        if url:
            try:
                response = method(url, params=params, headers=headers, data=data)
                # If we made a bad request (a 4XX client error or 5XX server error response),
                # we can raise it with Response.raise_for_status():"""
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # This is the error code for Not Authorized user(Expired Token)
                    # if this error code occurs, we raise exception
                    # AccessTokenHasExpired
                    raise AccessTokenHasExpired('Access token has expired.'
                                                ' User Id: %s' % user_id)
                # checks if error occurred on "Server" or is it a bad request
                elif e.response.status_code < 500:
                    if 'errors' in e.response.json():
                        error_message = e.message + ', Details: ' \
                                        + json.dumps(e.response.json().get('errors'))
                    elif 'error_description' in e.response.json():
                        error_message = e.message + ' , Details: ' \
                                        + json.dumps(e.response.json().get('error_description'))
                    else:
                        error_message = e.message
                else:
                    raise
                    # error_message = e.message
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
        module_name = 'social_network_service.' + social_network_name.lower()
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
    except AttributeError as e:
        raise ApiException('APIError: Unable to import module for required social network', error_code=500)
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


def get_utc_datetime(dt, timezone):
    """
    This method takes datetime object and timezone name and returns UTC specific datetime

    :Example:

        >>> now = datetime.datetime.now()  # datetime.datetime(2015, 10, 8, 11, 16, 55, 520914)
        >>> timezone = 'Asia/Karachi'
        >>> utc_datetime = get_utc_datetime(now, timezone) # '2015-10-08T06:16:55Z'

    :param dt: datetime object
    :type dt: datetime.datetime
    :return: timezone specific datetime object
    :rtype string
    """
    assert timezone, 'Timezone should not be none'
    assert isinstance(dt, datetime.datetime)
    # get timezone info from given datetime object
    local_timezone = pytz.timezone(timezone)
    local_dt = local_timezone.localize(dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

