"""
This module contains EventBase class which provides common methods for
all social networks that have event related functionality like save_event,
delete_event, process_events_rsvps etc.

To add another social network for events management, following are steps:

    + Add social network class which will handle authentication specific tasks.

        On the frontend side, redirect user to corresponding social network authentication
        page and then user will be redirected to our page (according to our settings)
        Now we need to send access and refresh token to Social Network API endpoint
        to add these credentials for current user.

        - get_access_and_refresh_token()
          Add this method which will get access and refresh token from social network
          API and then call save_user_credentials_in_db() which will save these credentials
          Refresh token will used to renew access token for this social network and user.

                Different social networks has different policies for access token expiration.

                - Access token for Meetup expires after an hour and can be refreshed
                  using "refresh" token

                - Access token for Eventbrite never expires if user does not change
                  his password on Eventbrite. we need to redirect the user to Eventbrite
                  authentication page to get new token.

                - Access token for Facebook expires after 59-60 days but when it expires,
                  we need to redirect the user to facebook authentication page to get new token.


        - get_member_id()
            This method gets user member id on corresponding social network.
            Every social network has it own way of getting member id using API calls.

        - validate_token()
            This method simply access some simple API endpoint of corresponding social network
            and checks whether it returns success or 401 error. If everything goes well, it
            returns True otherwise False

        - refresh_access_token()
            This method uses social network specific approach to get a fresh new token for
            user to get access to its API

        - validate_and_refresh_access_token()
            This method simply checks access token status using above validate_token()
            and it it gets False then it tries to refresh token using refresh_access_token()

        - save_user_credentials_in_db()
            This method saves user social network credentials in database

    + Add Event class for social network which will handle event related tasks.
        To add a new social network for events, we have to add a new class in
        social_network_service/event/ directory.

        Here we are following our own convention of naming modules and Classes which is as:
            If the name of social network is "Abc" then we need to create a module under
            "social_network_service/event/" with it name but all small letters like *abc.py*
            and class inside that module will be named "Abc" Title case single word.
            This class will inherit from "social_network_service.event.EventBase".

            This class will contain all method required to create, update, retrieve and delete
            events from that social network.

        Here is a list of event class method which commonly needed to impliment.

            - get_events()
                Impliment a method to retrieve events from social network

            - event_gt_to_sn_mapping():
                Impliment a method which will map getTalent specific data to social network
                specific data.

            - event_sn_to_gt_mapping():
                Impliment a method which will map social network specific event data
                to getTalent specific data.

            - create_event():
                Impliment a method which will do all task for creating event on socail network
                and on getTalent database.

            - update_even():
                It will impliment code to update an event on social network and on getTalent
                database.

            - add_location():
                Impliment a method which will create venue or location on social network for event.

            - unpublish_event():
                impliment a method which will unpublish or remove already created event on
                social network.


"""

# Standard Library
import json
from abc import ABCMeta
from abc import abstractmethod

# 3rd party
from flask import request

# Application Specific
from social_network_service.common.constants import HttpMethods
from social_network_service.common.models.db import db
from social_network_service.common.models.user import User
from social_network_service.common.models.event import Event
from social_network_service.common.models.misc import Activity
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.routes import EmailCampaignApiUrl
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.common.utils.datetime_utils import DatetimeUtils
from social_network_service.modules.urls import get_url
from social_network_service.social_network_app import logger
from social_network_service.common.models.venue import Venue
from social_network_service.modules.utilities import log_error
from social_network_service.modules.utilities import get_class
from social_network_service.custom_exceptions import NoUserFound, VenueNotFound
from social_network_service.custom_exceptions import EventNotSaveInDb
from social_network_service.custom_exceptions import EventNotUnpublished
from social_network_service.custom_exceptions import UserCredentialsNotFound
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls as Urls
from social_network_service.common.inter_service_calls.activity_service_calls import add_activity


class EventBase(object):
    """
    This class is base for all Social Network Specific Event classes and handles
    common functionality for event related tasks.

    It contains following methods:

    * __init__():
        This method is called by creating any child event class object.
        It sets initial values for event object e.g.
            It sets user, user_credentials, headers (authentication headers).
            It initializes event and rsvp list to empty list.

    * create_event() : abstract
        All child classes need to implement this method to create event on
        respective social network and in getTalent database.

    * event_sn_to_gt_mapping(): abstract
        This method maps/serializes event data from social network to getTalent
        specific data. Every child class has its own implementation for its
        event data.

    * event_gt_to_sn_mapping(): abstract
        This method maps/serializes event data from getTalent event data to social
        network specific data.
        Every child class has its own implementation for its event data.

    * pre_process_events():
        This method does not contain any implementation yet. But maybe in
        future it will contain some pre processing code for events.

    * process_events():
        Call this method after fetching events from social network.
        It maps social network event data to getTalent database specific data.
        It saves events in getTalent database after processing.

    * delete_event(event_id):
        This method calls 'unpublish_event() method of respective class to
        remove event from social network and then deletes this event from
        getTalent database.
        How it works:
        It takes integer id for event in getTalent database. It retrieves that
        event from database. If it finds any event with given id, it tries to
        unpublish that event otherwise returns False.

    * delete_events(array of ids):
        This method takes list or tuple of ids of events to be deleted.
        It then calls delete_event() method and returns two list of ids.
        One list for deleted events and other list contains ids of events that
        were not deleted.
        : returns deleted, not_deleted

    * get_events():
        Each child class has its own get_events() method to import/ extract
        events from respective social network.

    * get_events_from_db(start_date):
        This method returns all events for which event.start_date is after
        given date.

    * process_events_rsvps():
        This method imports RSVPs of all events for a specific user.

    * save_event(data):
        This method takes dictionary containing event data. It first checks if
        any event is there with given info (user_id, social_network_id,
        social_network_event_id), then it updates the existing event otherwise
        creates a new event in getTalent database.

    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        """
        This method takes User or UserSocialNetworkCredential object in kwargs
        and raises exception if no one is found.
        """
        self.events = []
        self.rsvps = []
        self.data = None
        self.headers = kwargs.get('headers')
        if not (kwargs.get('user_credentials') or kwargs.get('user')):
            raise UserCredentialsNotFound('User Credentials are empty/none')
        self.user_credentials = kwargs.get('user_credentials')
        self.user = kwargs.get('user') or User.get_by_id(self.user_credentials.user_id)
        self.social_network = kwargs.get('social_network')
        if isinstance(self.user, User):
            self.api_url = self.social_network.api_url
            self.member_id, self.access_token, self.refresh_token, self.webhook = self._get_user_credentials()
            self.venue_id = None
        else:
            error_message = "No User found in database with id %(user_id)s" % self.user_credentials.user_id
            raise NoUserFound('API Error: %s' % error_message)
        access_token = User.generate_jw_token(user_id=self.user.id)
        self.gt_headers = {
            'Content-Type': 'application/json',
            'Authorization': access_token
        }

    def _get_user_credentials(self):
        """
        This method get user_credentials for given user and returns a tuple
        containing member_id, access_token and refresh_token for user.
        :return: member_id, access_token, refresh_token, webhook
        :rtype: tuple
        """
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(self.user.id,
                                                                                         self.social_network.id)
        assert user_credentials is not None
        member_id = user_credentials.member_id
        access_token = user_credentials.access_token
        refresh_token = user_credentials.refresh_token
        webhook = user_credentials.webhook
        return member_id, access_token, refresh_token, webhook

    def archive_email_campaigns_for_deleted_event(self, event):
        """
        Whenever an event is deleted from social-network, we update field `is_deleted_from_vendor` to 1.
        We then check if it was promoted via email-campaign to getTalent candidates and mark all linked email-campaigns
        as archived.
        :param Event event: Event object
        """
        event.update(is_deleted_from_vendor=1)
        base_campaign_events = event.base_campaign_event
        for base_campaign_event in base_campaign_events:
            base_campaign = base_campaign_event.base_campaign
            email_campaigns = base_campaign.email_campaigns.all()
            for email_campaign in email_campaigns:
                data = {'is_hidden': 1}
                try:
                    response = http_request('patch', EmailCampaignApiUrl.CAMPAIGN % email_campaign.id,
                                            headers=self.gt_headers, data=json.dumps(data))
                    if response.ok:
                        logger.info('Email campaign(id:%s) has been archived successfully.' % email_campaign.id)
                    else:
                        logger.info('Email campaign(id:%s) could not be archived.' % email_campaign.id)
                except Exception:
                    logger.exception('Email campaign(id:%s) could not be archived.' % email_campaign.id)

    @abstractmethod
    def create_event(self, *args, **kwargs):
        """
        Each child class implements its own social network specific event
        creation code.
        """
        pass

    def get_event(self, event_url):
        """
        This method takes event resource uri, sends a GET call to respective social network API and then saves
        retrieved event in db.
        :param event_url: event resource rui
        :return: event model object
        :rtype type(t)
        """
        response = http_request('get', event_url, headers=self.headers)
        if response.ok:
            event = response.json()
            return self.import_event(event)

    def save_or_update_event(self, event_data):
        """
        This method takes event dictionary data and save that event in database or update the existing one
        if there is already event there with this data.
        :param event_data: event dict
        :rtype: Event
        """
        event = Event.get_by_user_id_social_network_id_vendor_event_id(self.user.id,
                                                                       self.social_network.id,
                                                                       event_data['social_network_event_id'])
        event_data['is_deleted_from_vendor'] = 0
        if event:
            event.update(**event_data)
            logger.info('Event updated successfully : %s' % event.to_json())
        else:
            event = Event(**event_data)
            Event.save(event)
            logger.info('Event imported successfully : %s' % event.to_json())
        return event

    def save_or_update_venue(self, venue_data):
        """
        This method takes venue dictionary data and save that venue in database or update the existing one
        if there is already venue there with this data.
        :param venue_data: venue dict
        :rtype: Venue
        """
        venue_in_db = Venue.get_by_user_id_and_social_network_venue_id(self.user.id,
                                                                       venue_data['social_network_venue_id'])
        if venue_in_db:
            venue_in_db.update(**venue_data)
            logger.info('Venue updated successfully:%s' % venue_in_db.to_json())
        else:
            venue_in_db = Venue(**venue_data)
            Venue.save(venue_in_db)
            logger.info('Venue imported successfully:%s' % venue_in_db.to_json())
        return venue_in_db

    @abstractmethod
    def event_sn_to_gt_mapping(self, event):
        """
        :param event: is likely the response from social network API
        :type event: dict
        While importing events, we need to map social network fields according
        to gt-database fields. Child classes will implement this.
        :param event:
        :return:
        """
        pass

    @staticmethod
    def validate_required_fields(data):
        social_network_id = data['social_network_id']
        user_id = data['user_id']
        venue_id = data['venue_id']
        venue = Venue.get_by_user_id_social_network_id_venue_id(
            user_id, social_network_id, venue_id)
        if not venue:
            raise VenueNotFound('Venue not found in database. Kindly create'
                                ' venue first.')
        
    @abstractmethod
    def event_gt_to_sn_mapping(self, data):
        """
        This function is used to map gt-fields to required social network
        fields for API calls. Child classes will implement this.
        :param data: data we get from Event creation form
        :type data: dict
        """
        # converting incoming Datetime object from Form submission into the
        # required format for API call
        start = data.get('start_datetime')
        end = data.get('end_datetime')
        data['start_datetime'] = DatetimeUtils.get_datetime_obj_if_format_is_valid(start)
        data['end_datetime'] = DatetimeUtils.get_datetime_obj_if_format_is_valid(end)

    def pre_process_events(self, events):
        """
        :param events: contains events of a particular user for a specific
            social network.
        :type events: list
        If we need any pre processing of events, we will implement the
        functionality here. For now, we don't do any pre processing.
        :param events:
        :return:
        """
        pass

    def process_events(self, events):
        """
        :param list events: contains events of a particular user for a specific social network.
        This is the function to process events once we have the events of some social network. It first maps the
        social network fields to gt-db fields. Then it checks if the event is present is db or not.
        If event is already in db, it updates the event fields otherwise it stores the event in db.
        Finally we import RSVPs of all the events in method post_process_events().
        """
        if events:
            self.pre_process_events(events)
        if events:
            logger.info('Events of %s(UserId: %s) are being processed to save in database.'
                        % (self.user.name, self.user.id))
            for event in events:
                try:
                    self.events.append(self.import_event(event))
                except Exception:
                    logger.exception('''Error occurred while importing event.
                                        UserId: %s,
                                        SocialNetworkId: %s
                                        Event: %s
                                     ''' % (self.user.id, self.social_network.id, event))

        if events:
            self.post_process_events()

    def post_process_events(self):
        """
        Once the event is stored in database after importing from social network, this function can be used to do
        some post processing. Now when all events of a user are imported, we import RSVPs for each event.
        """
        # Import RSVPs of events
        self.process_events_rsvps()

    def delete_event(self, event_id, is_delete_from_vendor=True):
        """
        Here we pass an event id, picks it from db, and try to delete
        it both from social network and database. If successfully deleted
        from both sources, returns True, otherwise returns False.
        :param event_id: is the 'id' of event present in our db
        :type event_id: int or long
        :param is_delete_from_vendor: is flag to delete event from third party
        :type is_delete_from_vendor: bool
        :return: True if deletion is successful, False otherwise.
        :rtype: bool
        """
        event = Event.get_by_user_and_event_id(self.user.id, event_id)
        if event:
            try:
                if is_delete_from_vendor:
                    self.unpublish_event(event.social_network_event_id)
                self.archive_email_campaigns_for_deleted_event(event)
                return True
            except Exception:  # some error while removing event
                logger.exception('delete_event: user_id: %s, event_id: %s, social network: %s(id: %s)'
                                 % (self.user.id, event.id, self.social_network.name, self.social_network.id))
        return False  # event not found in database

    def delete_events(self, event_ids):
        """
        :param event_ids: contains all the ids of events to be deleted
            both from social network and database.
        :type event_ids: list
        """
        deleted = []
        not_deleted = []
        if event_ids:
            for event_id in event_ids:
                event_obj = Event.get_by_user_and_event_id(user_id=request.user.id, event_id=event_id)
                title = event_obj.title
                if self.delete_event(event_id):
                    deleted.append(event_id)

                    activity_data = {'username': request.user.name,
                                     'event_title': title
                                     }
                    add_activity(user_id=request.user.id,
                                 activity_type=Activity.MessageIds.EVENT_DELETE,
                                 source_table=Event.__tablename__,
                                 source_id=event_id,
                                 params=activity_data)
                else:
                    not_deleted.append(event_id)
        return deleted, not_deleted

    def unpublish_event(self, event_id, method=HttpMethods.DELETE):
        """
        This function is used while running unit tests. It deletes the Event from database that were created
        during the lifetime of a unit test.
        :param int | long event_id: id of newly created event
        :param string method: http standard method , default is DELETE
        :return: True if event is deleted from vendor, False otherwise.
        :rtype: bool
        """
        # create url to unpublish event
        url = get_url(self, Urls.EVENT).format(event_id)
        # params are None. Access token is present in self.headers
        response = http_request(method, url, headers=self.headers, user_id=self.user.id)
        if response.ok:
            logger.info('|  Event has been unpublished (deleted)  |')
        else:
            error_message = "Event was not unpublished (deleted):%s" % response.text
            log_error({'user_id': self.user.id, 'error': error_message})
            raise EventNotUnpublished('ApiError: Unable to remove event from %s' % self.social_network.name)

    def get_events(self, *args, **kwargs):
        """
        This is used to get events from social_network. Child classes will
        implement this.
        """
        pass

    def import_event(self, event):
        """
        This method takes json event data from social network. It then maps that data to getTalent event
        and saves in db.
        :param event: json data for event
        :return: Event model object
        """
        self.user = db.session.merge(self.user)
        self.social_network = db.session.merge(self.social_network)
        event_data, venue_data = self.event_sn_to_gt_mapping(event)
        if venue_data:
            venue_in_db = self.save_or_update_venue(venue_data)
            event_data['venue_id'] = venue_in_db.id
        return self.save_or_update_event(event_data)

    def get_events_from_db(self, start_date=None):
        """
        This gets the events from database which starts after the specified start_date
        or in case date is None, return all events
        :param start_date:
        :type start_date: datetime|None
        :return: list of events
        """
        if start_date:
            events = Event.get_by_user_id_vendor_id_start_date(self.user.id, self.social_network.id, start_date)
        else:
            events = Event.filter_by_keywords(user_id=self.user.id, social_network_id=self.social_network.id)
        if events:
            logger.info('There are %s events of %s(user_id:%s) in database with start_datetime ahead of:%s.'
                        % (len(events), self.user.name, self.user.id, start_date))
        else:
            logger.info('No events found of %s(user_id:%s) in database with start_datetime ahead of:%s.'
                        % (self.user.name, self.user.id, start_date))
        return events

    def process_events_rsvps(self):
        """
        We import the RSVPs of all events present in self.events in this method.
        """
        # get_required class under rsvp/ to process RSVPs
        sn_rsvp_class = get_class(self.social_network.name, 'rsvp')
        # create object of selected RSVP class
        sn_rsvp_obj = sn_rsvp_class(user_credentials=self.user_credentials, headers=self.headers,
                                    social_network=self.social_network)
        # TODO: we might need this later
        # gets events of given Social Network from database
        # self.events = self.get_events_from_db(sn_rsvp_obj.start_date_dt)

        # get RSVPs of all events present in self.events using API of respective social network
        self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)
        # process RSVPs and save in database
        sn_rsvp_obj.process_rsvps(self.rsvps)

    def save_event(self):
        """
        This method takes dictionary containing event data. It first checks if
        any event is there with given info (user_id, social_network_id,
        social_network_event_id), then it updates the existing event otherwise
        creates a new event in getTalent database.
        Call this method after successfully publishing event on social network.
        :return event.id: id for event in getTalent database, that was created or updated
        :rtype event.id : int
        """
        data = self.data
        sn_event_id = data['social_network_event_id']
        social_network_id = data['social_network_id']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(self.user.id, social_network_id, sn_event_id)
        try:
            # if event exists in database, then update existing one.
            if event:
                del data['id']
                event.update(**data)
            else:
                # event not found in database, create a new one
                event = Event(**data)
                Event.save(event)
        except Exception as error:
            logger.exception('save_event: Event was not updated/saved in Database. '
                             'user_id: %s, event_id: %s, social network: %s(id: %s). Error:%s'
                             % (self.user.id, event.id, self.social_network.name, self.social_network.id,
                                error.message))
            raise EventNotSaveInDb('Error occurred while saving event in database')
        return event.id

