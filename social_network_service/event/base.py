from abc import ABCMeta, abstractmethod

from social_network_service import logger
from social_network_service.custom_exections import EventNotSaveInDb, \
    EventNotUnpublished
from social_network_service.utilities import log_error, get_class, \
    http_request, log_exception

from common.models.user import User
from common.models.event import Event
from common.models.user import UserCredentials
from common.models.social_network import SocialNetwork


class EventBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):

        self.events = []
        self.rsvps = []
        self.headers = kwargs.get('headers')
        self.user_credentials = kwargs.get('user_credentials')
        self.user = kwargs.get('user') or User.get_by_id(self.user_credentials.user_id)
        self.social_network = kwargs.get('social_network')
        assert isinstance(self.user, User)
        assert isinstance(self.social_network, SocialNetwork)
        self.api_url = self.social_network.api_url
        self.member_id, self.access_token, self.refresh_token, self.webhook = \
            self._get_user_credentials()
        self.url_to_delete_event = None
        self.venue_id = None

    def _get_user_credentials(self):
        user_credentials = UserCredentials.get_by_user_and_social_network_id(
            self.user.id, self.social_network.id
        )
        assert user_credentials is not None
        member_id = user_credentials.member_id
        access_token = user_credentials.access_token
        refresh_token = user_credentials.refresh_token
        webhook = user_credentials.webhook
        return member_id, access_token, refresh_token, webhook

    # def get_events(self, social_network):
    #     return self.get_events(social_network)

    @abstractmethod
    def create_event(self, *args, **kwargs):
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

    @abstractmethod
    def event_gt_to_sn_mapping(self, data):
        """
        This function is used to map gt-fields to required social network fields
        for API calls. Child classes will implement this.
        :param data:
        :return:
        """
        pass

    def get_event(self, id):
        pass

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

    def get_rsvps(self, user_credentials):
        """
        This gets the rsvps of events present in database and process
        them to save in database
        :param user_credentials:
        :return:
        """
        # get_required class under rsvp/ to process rsvps
        sn_rsvp_class = get_class(self.social_network.name, 'rsvp')
        # create object of selected rsvp class
        sn_rsvp_obj = sn_rsvp_class(social_network=self.social_network,
                                    headers=self.headers,
                                    user_credentials=user_credentials)
        # gets events of given Social Network from database
        self.events = self.get_events_from_db(sn_rsvp_obj.start_date_dt)
        if self.events:
            logger.debug('There are %s events of %s(UserId: %s) in database for '
                         'provided time range.\nSocial Network is %s'
                         % (len(self.events), self.user.name, self.user.id,
                            self.social_network.name))
        # process rsvps to save in database
        sn_rsvp_obj.process_rsvps(self.events)
        self.rsvps = sn_rsvp_obj.rsvps

    def save_event(self, data):
        """
        This function serves the storage of event in database after it is
        successfully published.
        :param data:
        :return:
        """
        sn_event_id = data['social_network_event_id']
        social_network_id = data['social_network_id']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(
            self.user.id,
            social_network_id,
            sn_event_id
        )
        try:
            if event:
                del data['id']
                event.update(**data)
            else:
                event = Event(**data)
                Event.save(event)
        except Exception as e:
            error_message = 'Event was not saved in Database\nError: %s' % e.message
            log_exception({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise EventNotSaveInDb('Error occurred while saving event in database')
        return event.id
