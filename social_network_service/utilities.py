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
import traceback
import importlib
from datetime import datetime
from dateutil.parser import parse
from requests_oauthlib import OAuth2Session

# Application Specific Imports
from common.models.user import User
from common.models.event import Event
from common.models.social_network import SocialNetwork

from social_network_service import logger
from social_network_service import flask_app as app
from social_network_service.custom_exections import ApiException, AccessTokenHasExpired
from social_network_service.custom_exections import SocialNetworkError, \
    SocialNetworkNotImplemented, InvalidDatetime, EventInputMissing


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
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def milliseconds_since_epoch(dt):
    assert isinstance(dt, datetime), 'input argument should be datetime object'
    return unix_time(dt) * 1000.0


def milliseconds_since_epoch_to_dt(epoch):
    return datetime.fromtimestamp(epoch / 1000.0)


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
    # length_of_frame = len(callee_frame)
    # no_of_items = list(range(0, length_of_frame-1))
    # no_of_item = None
    # selected_items = []
    # for item in no_of_items:
    #     # ignoring standard library files of python and pycharm
    #     if 'site-packages' not in callee_frame[item][1] \
    #             and 'pycharm' not in callee_frame[item][1]:
    #         selected_items.append(item)
    #     else:
    #         break
    # for item in selected_items:
    # if len(selected_items) - item == 4:
    #     no_of_item = item
    #     break

    no_of_item = 3
    #  We are using number 3 here, as
    # we call this function inside log_error() or log_exception()
    # which uses get_data_to_log(). get_data_to_log() calls get_callee_data().
    # So, here is the story,
    # index 0 has traceback of get_callee_data()
    # index 1 has traceback of get_data_to_log()
    # index 2 has traceback of log_error() or log_exception()
    # index 3 will have the traceback of function from where we call
    # log_error() or log_exception().
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
    if hasattr(log_data.get('error'), 'message') \
            or '400' in log_data['error']:
        callee_data = ("Reason: %(error)s, "
                       "User Id: %(user_id)s" % log_data)
        return callee_data
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
                if e.response.status_code in [401]:
                    # 401 is the error code for Not Authorized user(Expired Token)
                    # 400 is the error code for bad request
                    # raise AccessTokenHasExpired('Access token has expired.'
                    #                             ' User Id: %s' % user_id)
                    raise
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


def process_event(data, user_id, method='Create'):
    """
    This functions is called from restful POST service (which gets data from
    Event Create Form submission).
    It creates event on vendor as well as saves in database.
    Data in the arguments is the Data coming from Event creation form submission
    user_id is the id of current logged in user (which we get from session).
    """
    if data:
        social_network_id = data['social_network_id']
        social_network = SocialNetwork.get_by_id(social_network_id)
        # creating class object for respective social network
        social_network_class = get_class(social_network.name.lower(), 'social_network')
        event_class = get_class(social_network.name.lower(), 'event')
        sn = social_network_class(user_id=user_id)
        event_obj = event_class(user=sn.user,
                                headers=sn.headers,
                                social_network=social_network)

        data['user_id'] = user_id
        # converting incoming Datetime object from Form submission into the
        # required format for API call
        try:
            start = data['start_datetime']
            end = data['end_datetime']
            if not all([start, end]):
                raise
        except Exception as e:
            raise EventInputMissing("DateTimeError: Unable to find datetime inputs")
        try:
            data['start_datetime'] = parse(start)
            data['end_datetime'] = parse(end)
            if data['start_datetime'] < datetime.now() or data['end_datetime'] < datetime.now():
                raise InvalidDatetime('Invalid DateTime')
        except InvalidDatetime as e:
            raise InvalidDatetime('Invalid DateTime: start_datetime and end_datetime should '
                                  'be in future.')
        except Exception as e:
            raise InvalidDatetime('Invalid DateTime: Kindly specify datetime in ISO format')
        # posting event on social network

        event_obj.event_gt_to_sn_mapping(data)
        if method == 'Create':
            event_obj.create_event()
        else:
            event_obj.update_event()

        if event_obj.data['social_network_event_id']:  # Event has been successfully published on vendor
            # save event in database
            gt_event_id = event_obj.save_event()
            return gt_event_id
    else:
        error_message = 'Data not received from Event Creation/Edit FORM'
        log_error({'user_id': user_id,
                   'error': error_message})


def delete_events(user_id, event_ids):
    assert len(event_ids) > 0, 'event_ids should contain at least one event id'
    if event_ids:
        social_networks = {}
        deleted, not_deleted = [], []
        for event_id in event_ids:
            event = Event.get_by_user_and_event_id(user_id, event_id)
            if event:
                social_network = event.social_network
                if social_network.id not in social_networks:
                    social_network_class = get_class(social_network.name.lower(), 'social_network')
                    event_class = get_class(social_network.name.lower(), 'event')
                    sn = social_network_class(user_id=user_id, social_network_id=social_network.id)
                    event_obj = event_class(user=sn.user,
                                            social_network=social_network,
                                            headers=sn.headers)
                    social_networks[social_network.id] = dict(event_obj=event_obj,
                                                              event_ids=[event_id])
                else:
                    social_networks[social_network.id]['event_ids'].append(event_id)
            else:
                not_deleted.append(event_id)
        for _, social_network in social_networks.items():
            event_obj = social_network['event_obj']
            dltd, nt_dltd = event_obj.delete_events(social_network['event_ids'])
            deleted.extend(dltd)
            not_deleted.extend(nt_dltd)
        return deleted, not_deleted
    else:
        error_message = 'event_ids should contain at least one event id'
        log_error(
            dict(
                error=error_message,
                user=user_id,
            )
        )


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

        >>> now = datetime.now()  # datetime.datetime(2015, 10, 8, 11, 16, 55, 520914)
        >>> timezone = 'Asia/Karachi'
        >>> utc_datetime = get_utc_datetime(now, timezone) # '2015-10-08T06:16:55Z'

    :param dt: datetime object
    :type dt: datetime.datetime
    :return: timezone specific datetime object
    :rtype string
    """
    assert timezone, 'Timezone should not be none'
    assert isinstance(dt, datetime)
    # get timezone info from given datetime object
    local_timezone = pytz.timezone(timezone)
    local_dt = local_timezone.localize(dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def add_organizer_venue_data(event):
    """
    When a user requests for events or a single event data, we return event data which contains
    associated venue and organizer objects data as well.
    If venue or organizer is None for this event, we add empty dict {} for venue or organizer data.

    We are adding associated organizer and venue data in event data here.
    This method takes an event (Event) object and then returns json data which contains
    event data as well as organizer and venue

    .. Example:

        - Pass event object to this method
        - it will return data like this
        - Sample Output:
            {
                "cost": 0,
                "currency": "USD",
                "description": "Test Event Description",
                "end_datetime": "2015-10-27 16:40:57",
                "group_id": "18837246",
                "group_url_name": "QC-Python-Learning",
                "id": 200,
                "max_attendees": 10,
                "organizer": {
                                  "about": "I am a software engineer",
                                  "email": "mzohaib.qc@gmail.com",
                                  "id": 1,
                                  "name": "Zohaib Ijaz",
                                  "user_id": 1
                            },
                "registration_instruction": "Just Come",
                "social_network_event_id": "225893535",
                "social_network_id": 13,
                "start_datetime": "2015-10-17 16:40:57",
                "tickets_id": "",
                "timezone": "Asia/Karachi",
                "title": "Meetup Test Event",
                "url": "",
                "user_id": 1,
                "venue": {
                              "address_line1": "Infinite Loop",
                              "address_line2": "",
                              "city": "Cupertino",
                              "country": "us",
                              "id": 1,
                              "latitude": -120,
                              "longitude": 31,
                              "social_network_id": 13,
                              "social_network_venue_id": "15570022",
                              "state": "CA",
                              "user_id": 1,
                              "zipcode": "95014"
                        }
              }

    :param event: model object
    :return: dictionary containing event data plus organizer and venue data
    :rtype dict:
    """
    event_data = event.to_json()
    # add organizer data under organizer key
    event_data['organizer'] = event.organizer.to_json() if event.organizer else {}
    del event_data['organizer_id']
    # add venue data under venue key
    event_data['venue'] = event.venue.to_json() if event.venue else {}
    del event_data['venue_id']
    return event_data

