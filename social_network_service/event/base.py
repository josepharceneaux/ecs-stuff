"""
This module contains EventBase class which provides common methods for
all social networks that have event related functionality like save_event, delete_event,
process_events_rsvps etc.

To add another social network for events management, following are steps:

    + Add social network class which will handle authentication specific tasks.
    + Add Event class for this social network which will handle event related tasks.

"""

# Standard Library
from abc import ABCMeta
from abc import abstractmethod

# Application Specific
from datetime import datetime
from dateutil.parser import parse
from common.models.user import User
from common.models.event import Event
from common.models.user import UserCredentials
from social_network_service import logger
from social_network_service.utilities import log_error
from social_network_service.utilities import get_class
from social_network_service.utilities import http_request
from social_network_service.utilities import log_exception
from social_network_service.custom_exections import NoUserFound, InvalidDatetime
from social_network_service.custom_exections import EventNotSaveInDb
from social_network_service.custom_exections import EventNotUnpublished
from social_network_service.custom_exections import UserCredentialsNotFound


class EventBase(object):
    """
    This class is base for all Social Network Specific Event classes and handles common
    functionality for event related tasks.

    It contains following methods:

    * __init__():
        This method is called by creating any child event class object.
        It sets initial values for event object e.g.
            It sets user, user_credentials, headers (authentication headers)
            It initializes event and rsvp list to empty list.

    * create_event() : abstract
        All child classes need to implement this method to create event on
        respective social network and in getTalent database

    * event_sn_to_gt_mapping(): abstract
        This method maps/serializes event data from social network to getTalent specific data.
        Every child class has its own implementation for its event data.

    * event_gt_to_sn_mapping(): abstract
        This method maps/serializes event data from getTalent event data social network specific data.
        Every child class has its own implementation for its event data.

    * pre_process_events():
        This method does not contain any implementation yet. But maybe in future it
        will contain some pre processing code for events.

    * process_events():
        Call this method after fetching events from social network.
        It maps social network event data to getTalent database specific data.
        It saves events in getTalent database after processing.

    * delete_event(event_id):
        This method calls 'unpublish_event() method of respective class to remove event
        from social network and then deletes this event from getTalent database.
        How it works:
        It takes integer id for event in getTalent database. It retrieves that  event from database.
        If it finds any event with given id, it tries to unpublish that event otherwise returns False.

    * delete_events(array of ids):
        This method takes list or tuple of ids of events to be deleted.
        It then calls delete_event() method and returns two list of ids.
        One list for deleted events and other list contains ids of events that were not deleted.
        : returns deleted, not_deleted

    * get_events():
        Each child class has its own get_events() method to import/ extract events from respective
        social network.

    * get_events_from_db(start_date):
        This method returns all events for which event.start_date is after given date.

    * process_events_rsvps():
        This method imports RSVPs of all events for a specific user.

    * save_event(data):
        This method takes dictionary containing event data. It first checks if any event is there
        with given info (user_id, social_network_id, social_network_event_id), then it updates
        the existing event otherwise creates a new event in getTalent database.

    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        """
        This method takes User or UserCredentials object in kwargs and raises exception if no one is found.

        :param args:
        :param kwargs:
        :return:
        """
        self.events = []
        self.rsvps = []
        self.data = None
        self.headers = kwargs.get('headers')
        if kwargs.get('user_credentials') or kwargs.get('user'):
            self.user_credentials = kwargs.get('user_credentials')
            self.user = kwargs.get('user') or User.get_by_id(
                self.user_credentials.user_id)
            self.social_network = kwargs.get('social_network')
            if isinstance(self.user, User):
                self.api_url = self.social_network.api_url
                self.member_id, self.access_token, self.refresh_token, self.webhook = \
                    self._get_user_credentials()
                self.url_to_delete_event = None
                self.venue_id = None
            else:
                error_message = "No User found in database with id %(user_id)s" \
                            % self.user_credentials.user_id
                raise NoUserFound('API Error: %s' % error_message)
        else:
            raise UserCredentialsNotFound('User Credentials are empty/none')

    def _get_user_credentials(self):
        """
        This method get user_credentials for given user and returns a tuple containing
        member_id, access_token and refresh_token for user.
        :return:
        """
        user_credentials = UserCredentials.get_by_user_and_social_network_id(
            self.user.id, self.social_network.id
        )
        assert user_credentials is not None
        member_id = user_credentials.member_id
        access_token = user_credentials.access_token
        refresh_token = user_credentials.refresh_token
        webhook = user_credentials.webhook
        return member_id, access_token, refresh_token, webhook

    @abstractmethod
    def create_event(self, *args, **kwargs):
        """
        Each child class implements its own social network specific event creation code.
        :param args:
        :param kwargs:
        :return:
        """
        pass

    @abstractmethod
    def event_sn_to_gt_mapping(self, event):
        """
        While importing events, we need to map social network fields according
        to gt-database fields. Child classes will implement this.
        :param event:
        :return:
        """
        pass

    def event_gt_to_sn_mapping(self, data):
        """
        This function is used to map gt-fields to required social network fields
        for API calls. Child classes will implement this.
        :param data:
        :return:
        """
        # converting incoming Datetime object from Form submission into the
        # required format for API call
        try:
            start = data['start_datetime']
            end = data['end_datetime']
            data['start_datetime'] = parse(start)
            data['end_datetime'] = parse(end)
        except Exception as e:
            raise InvalidDatetime('Invalid DateTime: Kindly specify datetime in UTC format like 2015-10-08T06:16:55Z')

    def pre_process_events(self, events):
        """
        If we need any pre processing of events, we will implement the
        functionality here. For now, we don't do any pre processing.
        :param events:
        :return:
        """
        pass

    def process_events(self, events):
        """
        This is the function to process events once we have the events of
        some social network. It first maps the social network fields to
        gt-db fields. Then it checks if the event is present is db or not.
        If event is already in db, it updates the event fields otherwise
        it stores the event in db.
        :param events:
        :return:
        """
        if events:
            self.pre_process_events(events)
        if events:
            logger.debug('Events of %s(UserId: %s) are being processed '
                         'to save in database.'
                         % (self.user.name, self.user.id))
            for event in events:
                event = self.event_sn_to_gt_mapping(event)
                if event:
                    event_in_db = \
                        Event.get_by_user_and_social_network_event_id(
                            event.user_id,
                            event.social_network_event_id)
                    try:
                        if event_in_db:
                            data = dict(title=event.title,
                                        description=event.description,
                                        start_datetime=event.start_datetime,
                                        end_datetime=event.end_datetime,
                                        url=event.url,
                                        timezone=event.timezone,
                                        max_attendees=event.max_attendees)
                            event_in_db.update(**data)
                        else:
                            Event.save(event)
                    except Exception as error:
                        error_message = 'Cannot process an event. Social ' \
                                        'network: %s. Details: %s' \
                                        % (self.social_network.id,
                                           error.message)
                        log_exception({
                            'user_id': self.user.id,
                            'error': error_message,
                        })
            logger.debug('%s Event(s) of %s(UserId: %s) has/have been '
                         'saved/updated in database.'
                         % (len(events), self.user.name, self.user.id))
        if events:
            self.post_process_events(events)

    def post_process_events(self, events):
        """
        Once the event is stored in database after importing from social
        network, this function can be used to some post processing.
        For now, we don't do any post processing
        :param events:
        :return:
        """
        pass

    def delete_event(self, event_id):
        """
        Here we pass an event id, picks it from db, and try to delete
        it both from social network and database. If successfully deleted
        from both sources, returns True, otherwise returns False
        :param event_id:
        :return:
        """
        event = Event.get_by_user_and_event_id(self.user.id, event_id)
        if event:
            try:
                self.unpublish_event(event.social_network_event_id)
                Event.delete(event_id)
                return True
            except Exception as error:  # some error while removing event
                log_exception({
                    'user_id': self.user.id,
                    'error': error.message,
                })
                return False
        return False  # event not found in database

    def delete_events(self, event_ids):

        deleted = []
        not_deleted = []
        if event_ids:
            for event_id in event_ids:
                if self.delete_event(event_id):
                    deleted.append(event_id)
                else:
                    not_deleted.append(event_id)

        return deleted, not_deleted

    def unpublish_event(self, event_id, method='POST'):
        """
        This function is used when run unit test. It deletes the Event from
        meetup which was created in the unit testing.
        :param event_id:id of newly created event
        :return: True if event is deleted from vendor, False other wsie
        """
        # create url to publish event
        url = self.url_to_delete_event
        # params are None. Access token is present in self.headers
        response = http_request(method, url, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            logger.info('|  Event has been unpublished (deleted)  |')
        else:
            error_message = "Event was not unpublished (deleted)."
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise EventNotUnpublished('ApiError: '
                                      'Unable to remove event from %s'
                                      % self.social_network.name)

    def get_events(self, *args, **kwargs):
        """
        This is used to get events from social_network. Child classes will
        implement this.
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def get_events_from_db(self, start_date):
        """
        This gets the events from database which starts after the specified start_date
        :param start_date:
        :return:
        """
        if start_date:
            return Event.get_by_user_id_vendor_id_start_date(self.user.id,
                                                             self.social_network.id,
                                                             start_date
                                                             )

    def process_events_rsvps(self, user_credentials, rsvp_data=None):
        """
        We get events against a particular user_credential.
        Then we get the rsvps of all events present in database and process
        them to save in database.
        :param user_credentials:
        :return:
        """
        # get_required class under rsvp/ to process rsvps
        sn_rsvp_class = get_class(self.social_network.name, 'rsvp')
        # create object of selected rsvp class
        sn_rsvp_obj = sn_rsvp_class(user_credentials=user_credentials,
                                    headers=self.headers,
                                    social_network=self.social_network
                                    )

        # gets events of given Social Network from database
        self.events = self.get_events_from_db(sn_rsvp_obj.start_date_dt)
        if self.events:
            logger.debug('There are %s events of %s(UserId: %s) in database '
                         'within provided time range.'
                         % (len(self.events), self.user.name, self.user.id))
        else:
            logger.debug('No events found of %s(UserId: %s) in database '
                         'within provided time range.'
                         % (self.user.name, self.user.id))

        # get RSVPs of all events present in self.events using API of
        # respective social network
        self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)
        # process RSVPs and save in database
        sn_rsvp_obj.process_rsvps(self.rsvps)

    def save_event(self):
        """
        This method takes dictionary containing event data. It first checks if any event is there
        with given info (user_id, social_network_id, social_network_event_id), then it updates
        the existing event otherwise creates a new event in getTalent database.

        Call this method after successfully publishing event on social network.

        :param data: dictionary containing data for event to be saved
        :type data: dictionary
        :return event.id: id for event that was created or updated
        :rtype event.id : int
        """
        data = self.data
        sn_event_id = data['social_network_event_id']
        social_network_id = data['social_network_id']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(
            self.user.id,
            social_network_id,
            sn_event_id
        )
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
            log_exception({
                'user_id': self.user.id,
                'error': 'Event was not saved in Database\nError: %s' % error.message
            })
            raise EventNotSaveInDb('Error occurred while saving event in database')
        return event.id
