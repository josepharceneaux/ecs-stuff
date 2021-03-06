"""
This file contains some (supposedly) common utility functions that may be used
or consumed by various programs.
"""

# Standard Library
import fnmatch
import glob
import imp
import importlib
import inspect
import os
import random
import re
import string
import sys
import traceback
from datetime import datetime

# Third Party
from flask import request
from pytz import timezone

# Application Specific Imports
from social_network_service.common.error_handling import InvalidUsage, ResourceNotFound
from social_network_service.common.inter_service_calls.activity_service_calls import add_activity
from social_network_service.common.models.misc import Activity
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.utils.handy_functions import snake_case_to_camel_case
from social_network_service.custom_exceptions import *
from social_network_service.common.models.event import Event
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.constants import MEETUP
from social_network_service.social_network_app import logger


class Attendee(object):
    """
    Basically a placeholder object that will be used while processing
    RSVPs. See base.py
    """

    def __init__(self, *args, **kwargs):
        self.first_name = None  # first name of attendee
        self.last_name = None  # last name of attendee
        self.full_name = None  # full name of attendee
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
        self.candidate_source_id = None  # attendee's candidate_source id
        # from db
        self.source_product_id = None  # attendee's source product id in database
        self.social_profile_url = None

    def __str__(self):
        return 'Name: %s, RSVP_ID: %s, EMAIL: %s' % (self.full_name,
                                                     self.rsvp_id,
                                                     self.email)


def unix_time(dt):
    """
    Converts dt(UTC) datetime object to epoch in seconds
    :param dt:
    :type dt: datetime
    :return: returns epoch time in milliseconds.
    :rtype: long
    """
    epoch = datetime(1970, 1, 1, tzinfo=timezone('UTC'))
    delta = dt - epoch
    return delta.total_seconds()


def milliseconds_since_epoch(dt):
    """
    Converts dt(UTC) datetime object to epoch in milliseconds
    :param dt:
    :type dt: datetime
    :return: returns epoch time in milliseconds.
    :rtype: long
    """
    assert isinstance(dt, datetime), 'input argument should be datetime object'
    return unix_time(dt) * 1000.0


def milliseconds_since_epoch_local_time(dt):
    """
    Converts dt(local time) datetime object to epoch in milliseconds
    :param dt:
    :type dt: datetime
    :return: returns epoch time in milliseconds.
    :rtype: long
    """
    assert isinstance(dt, datetime), 'input argument should be datetime object'
    return int(dt.strftime("%s")) * 1000


def milliseconds_since_epoch_to_dt(epoch, tz=timezone('UTC')):
    return datetime.fromtimestamp(epoch / 1000.0, tz=tz)


def get_callee_data(app_name=None):
    """
    This is used to get the data of callee, i.e. the function where
    error is logged. We can say it gives the traceback info but in more
    precise way by giving file_name, line_no, function_name and class_name
    if any.
    :param app_name:
    :return: callee_data
    :rtype: dict
    """
    current_frame = inspect.currentframe()
    callee_frame = inspect.getouterframes(current_frame, 2)
    if app_name == 'social_network_service':
        no_of_item = 3
        if callee_frame[no_of_item][3] == 'http_request':
            no_of_item = 4
        # We are using number 3 here, as
        # we call this function inside log_error()
        # which uses get_data_to_log().
        # get_data_to_log() calls get_callee_data().
        # So, here is the story,
        # index 0 has traceback of get_callee_data()
        # index 1 has traceback of get_data_to_log()
        # index 2 has traceback of log_error()
        # index 3 will have the traceback of function from where we call
        # log_error().
        # Another case is logging inside http_request. For this we need
        # traceback of the function from where http_request was called.
    else:
        no_of_item = None
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
    """
    callee_data = get_data_to_log(log_data)
    logger.error(callee_data)


def get_data_to_log(log_data):
    """
    :param log_data:  is a dict which contains error details and User Id in
            keys 'error'  in 'user_id' respectively.

    - We first get the information of callee using get_callee_data(),
        and append user_id_and_error_message in it. Finally we return the
        descriptive error message.

    - This function is called from log_error() defined in
        social_network_service/utilities.py

    ** See Also:
        - Have a look on log_error() defined in
        social_network_service/utilities.py
    :return: callee_data which contains the useful information of traceback
            like Reason of error, function name, file name, user id etc.
    :rtype: dict
    """
    if hasattr(log_data.get('error'), 'message'):
        callee_data = ("Reason: %(error)s, "
                       "User Id: %(user_id)s" % log_data)
        return callee_data
    # get_callee_data() returns the dictionary of callee data
    callee_data_dict = get_callee_data(app_name='social_network_service')
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


def get_class(social_network_name, category, user_credentials=None):
    """
    This function is used to import module from given parameters.
    Here we pass following parameters
    :param social_network_name:
    :param category:
    :return: import the required class and return it
    """
    module_name = 'social_network_service.modules.' + category + '.' + social_network_name.lower()
    try:
        module = importlib.import_module(module_name)
        _class = getattr(module, social_network_name.title())
    except ImportError:
        error_message = 'Social Network "%s" is not allowed for now, ' \
                        'please implement code for this social network.' \
                        % social_network_name
        log_error({'user_id': user_credentials.user_id if user_credentials else '',
                   'error': error_message})
        raise SocialNetworkNotImplemented('Import Error: Unable to import '
                                          'module for required social network')
    except AttributeError:
        raise SocialNetworkNotImplemented('Unable to import module for required '
                                          'social network')
    return _class


def process_event(data, user_id, method='Create'):
    """
    This functions is called from restful POST service (which gets data from
    Event Create Form submission).
    It creates event on vendor as well as saves in database.
    Data in the arguments is the Data coming from Event creation form submission
    user_id is the id of current logged in user (which we get from session).
    :return: id of event
    :rtype: int
    """
    if data:
        social_network_id = data.get('social_network_id', 0)
        social_network = SocialNetwork.get(social_network_id)
        if social_network:
            # creating class object for respective social network
            social_network_class = get_class(social_network.name.lower(), 'social_network')
            event_class = get_class(social_network.name.lower(), 'event')
            sn = social_network_class(user_id=user_id)
            event_obj = event_class(user=sn.user, headers=sn.headers, social_network=social_network)
        else:
            raise SocialNetworkError('Unable to find social network')
        data['user_id'] = user_id
        if social_network.name.lower() == MEETUP and data.get('organizer_id'):
            raise InvalidUsage('organizer_id is not a valid field in case of meetup')
        event_obj.event_gt_to_sn_mapping(data)

        activity_data = {'username': request.user.name}

        if method == 'Create':
            event_id = event_obj.create_event()

            # Create activity of event object creation
            event_obj = Event.get_by_user_and_event_id(user_id=user_id, event_id=event_id)
            activity_data.update({'event_title': event_obj.title})
            add_activity(user_id=user_id,
                         activity_type=Activity.MessageIds.EVENT_CREATE,
                         source_id=event_id,
                         source_table=Event.__tablename__,
                         params=activity_data)
            return event_id
        else:
            event_id = event_obj.update_event()

            # Create activity of event object creation
            event_obj = Event.get_by_user_and_event_id(user_id=user_id,
                                                       event_id=event_id)

            activity_data.update({'event_title': event_obj.title})

            add_activity(user_id=user_id,
                         activity_type=Activity.MessageIds.EVENT_UPDATE,
                         source_id=event_id,
                         source_table=Event.__tablename__,
                         params=activity_data)

            return event_id
    else:
        error_message = 'Data not received from Event Creation/Edit FORM'
        log_error({'user_id': user_id,
                   'error': error_message})


def delete_events(user_id, event_ids):
    """
    This utility function takes a list of event ids and id of user who owns the events.
    This function first create a mappings dictionary for which looks like this

            social_networks = {
                    # keys are Ids, and values are corresponding Social Network object and event ids
                    "13" : {
                              "event_obj": Meetup obj,
                              "event_ids" : [1,2,4]
                            },
                    "18" : {
                              "event_obj": Eventbrite obj,
                              "event_ids" : [33,45]
                            }

                }
    We then iterate this dictionary and call delete_events() method on respective social
     network objects.

    :param user_id:
    :param event_ids:
    :return: deleted(events that have been deleted), not_deleted (events that weren't deleted)
    :rtype: tuple (list, list)
    """
    assert len(event_ids) > 0, 'event_ids should contain at least one event id'
    # dictionary for mappings
    social_networks = {}
    # list for event id that are deleted successfully and that were not delete due to any reason
    deleted, not_deleted = [], []
    # iterate through all event ids
    for event_id in event_ids:
        # get event from database for this user and event id
        event = Event.get_by_user_and_event_id(user_id, event_id)
        # if event was not found then it means that, either this event does not exists at all
        # or this user does not create that event, so he is not allowed to get that so push this
        # event id in not_delete list.
        if event and not event.is_deleted_from_vendor:
            # get social network from event
            social_network = event.social_network
            # social network id is already in mapping dictionary then just add this event id in
            # its specific event ids list otherwise create a new dictionary with
            #  social_network id as key
            # and set social network object and ids list for events
            if social_network.id not in social_networks:
                # get social network and event management class for this social network
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
            # if event was not found, put this id in not_deleted list
            not_deleted.append(event_id)

    for social_network_id, social_network in social_networks.items():
        # get event object from mapping dictionary and invoke delete_events on this to
        #  unpublish / remove
        # social network specific actions
        event_obj = social_network['event_obj']
        successful, unsuccessful = event_obj.delete_events(social_network['event_ids'])
        deleted.extend(successful)
        not_deleted.extend(unsuccessful)

    return deleted, not_deleted


def camel_case_to_snake_case(name):
    """ Convert camel case to underscore case
        socialNetworkId --> social_network_id

            :Example:

                result = camel_case_to_snake_case('socialNetworkId')
                assert result == 'social_network_id'

    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('(.)([0-9]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def camel_case_to_title_case(name):
    """ Converts camel case to title case
        social_network_id --> Social Network Id

            :Example:

                result = camel_case_to_title_case('social_network_id')
                assert result == 'Social Network Id'
    """
    name_ = camel_case_to_snake_case(name)
    return ' '.join(name_.split('_')).title()


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
    - We have a module facebook-sdk in this project which is imported as
        import facebook
    Also we have Facebook classes defined by ourselves inside
    social_network_service/. So when we import facebook inside our classes
    (e.g import facebook in  social_network_service/rsvp/facebook.py), we have
    name conflict.
    - This function is used to import facebook-sdk module rather than local
    module named as facebook.
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
                "social_network_group_id": "18837246",
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
                              "address_line_1": "Infinite Loop",
                              "address_line_2": "",
                              "city": "Cupertino",
                              "country": "us",
                              "id": 1,
                              "latitude": -120,
                              "longitude": 31,
                              "social_network_id": 13,
                              "social_network_venue_id": "15570022",
                              "state": "CA",
                              "user_id": 1,
                              "zip_code": "95014"
                        }
              }

    :param event: model object
    :return: dictionary containing event data plus organizer and venue data
    :rtype dict:
    """
    event_data = event.to_json()
    # add organizer data under organizer key
    event_data['event_organizer'] = event.event_organizer.to_json() if event.event_organizer else {}
    del event_data['organizer_id']
    # add venue data under venue key
    event_data['venue'] = event.venue.to_json() if event.venue else {}
    del event_data['venue_id']
    return event_data


def get_random_word(length):
    """
    This function takes a number as an input and creates a random string of length
    specified by given number.
    :param length: int or long
    :return:
    """
    return ''.join(random.choice(string.lowercase) for _ in xrange(length))


def is_token_valid(social_network_id, user_id):
    # Get social network specified by social_network_id
    social_network = SocialNetwork.get_by_id(social_network_id)
    if social_network:
        user_social_network_credential = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            user_id, social_network_id)
        if user_social_network_credential:
            # Get social network specific Social Network class
            social_network_class = get_class(social_network.name, 'social_network')
            # create social network object which will validate
            # and refresh access token (if possible)
            sn = social_network_class(user_id=user_id,
                                      social_network_id=social_network.id
                                      )
            return sn.access_token_status, social_network.name
        return False, social_network.name
    else:
        raise ResourceNotFound("Invalid social network id given")


def get_file_matches(file_name, dir_path):
    """
    This function given a name of file in given directory path, returns full path of all files matching given name.
    :param str file_name: file name to search
    :param str dir_path: directory in which file name will be searched
    :return: list of file paths
    :rtype: list
    """
    matches = []
    for root, dirnames, filenames in os.walk(dir_path):
        for filename in fnmatch.filter(filenames, file_name):
            matches.append(os.path.join(root, filename))
    return matches


def get_test_info(path):
    """
    This functions given a directory path, returns all test modules, classes and functions.
    :param str path: root test directory path
    :return: dictionary
    :rtype: dict
        :Output:
            For SocialNetwork Service, here is a partial output:
            {
                 "test_v1_graphql_sn_api_tests": {
                    "functions": [
                      "test_get_events_pagination",
                      "test_get_subscribed_social_network",
                      "test_get_venue"
                    ]
                  },
                "test_v1_importer": {
                    "classes": {
                      "Test_Event_Importer": [
                        "test_eventbrite_rsvp_importer_endpoint"
                      ]
                    },
                    "functions": [
                      "test_event_import_to_update_existing_event",
                      "test_event_import_to_create_new_event"
                    ]
                  },
                "test_v1_organizer_api": {
                    "classes": {
                      "TestOrganizers": ["test_get_with_valid_token"]
                    }
                }
            }
    """
    result = {}
    files = list()
    modules = []
    for f in glob.glob(path + "/*/test_*.py") + glob.glob(path + "/test_*.py"):
        name = os.path.basename(f)[:-3]
        files.append(name)
        module = imp.load_source(name, f)
        modules.append(module)
    for module in modules:
        module_name = module.__name__
        result[module_name] = {
            'classes': {},
            'functions': []
        }
        for class_name in filter(lambda x: x.startswith('Test'), dir(module)):
            klass = getattr(module, class_name)
            methods = filter(lambda x: x.startswith('test_'), klass.__dict__.keys())
            result[module_name]['classes'][class_name] = methods
        result[module_name]['functions'] = filter(lambda x: x.startswith('test_'), module.__dict__.keys())
    return result
