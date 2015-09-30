
from abc import ABCMeta, abstractmethod
from social_network_service.custom_exections import EventNotSaveInDb
from social_network_service.utilities import get_message_to_log, log_error
from gt_common.models.event import Event
from gt_common.models.user import User
from gt_common.models.user import UserCredentials
from gt_common.models.social_network import SocialNetwork


class EventBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):

        self.events = []
        self.rsvps = []
        self.headers = kwargs['headers']
        self.user = kwargs.get('user') or None
        self.social_network = kwargs.get('social_network') or None
        # TODO We should get the user & social network in Social network base
        assert isinstance(self.user, User)
        assert isinstance(self.social_network, SocialNetwork)
        self.user_id = self.user.id # TODO find a better way
        self.api_url = self.social_network.api_url
        self.member_id, self.access_token, self.refresh_token, self.webhook = \
            self._get_user_credentials()

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

    def get_events(self, social_network):
        return self.get_events(social_network)

    def get_event(self, id):
        pass

    def create_event(self):
        pass

    def normalize_event(self, event):
        pass

    def pre_process_events(self, events):
        pass

    def process_events(self, events):
        if events:
            self.pre_process_events(events)
        for event in events:
            event = self.normalize_event(event)
            if event:
                event_in_db = Event.get_by_user_and_vendor_id(event.user_id,
                                                              event.social_network_event_id)
                try:
                    if event_in_db:
                        data = dict(title=event.title,
                                    description=event.description,
                                    start_datetime=event.start_datetime,
                                    end_datetime=event.end_datetime)
                        event_in_db.update(**data)
                    else:
                        Event.save(event)
                except Exception as error:
                    error_message = 'Cannot process an event. Social network: %s. Details: %s' % (
                                    self.social_network.id, error.message
                    )
                    log_error({
                            'error' : error_message,
                            'functionName': 'process_events',
                            'fileName': __file__,
                            'user': self.user.id,
                    })
                    # Now let's try to process the next event
        if events:
            self.post_process_events(events)

    def post_process_events(self, events):
        pass

    @abstractmethod
    def create_event(self, *args, **kwargs):
        pass

    def delete_events(self, event_ids):
        #TODO why we are not passing list of 'events' here?
        deleted = []
        not_deleted = []
        if len(event_ids) > 0:
            for event_id in event_ids:
                event = Event.get_by_user_and_event_id(self.user_id, event_id)
                if event:
                    try:
                        self.unpublish_event(event.vendor_event_id)
                        Event.delete(event_id)
                        deleted.append(event_id)
                    except Exception as e:     # some error while removing event
                        log_error({
                            'Reason':e.message,
                            'functionName': 'delete_events',
                            'fileName': __file__,
                            'User': self.user.id
                        })
                        not_deleted.append(event_id)
                        # TODO I think we shouldn't use not_deleted
                else:
                    not_deleted.append(event_id)
        return deleted, not_deleted

    def get_events(self, *args, **kwargs):
        pass

    def save_event(self, data):
        """
        This function serves the storage of event in database after it is
        successfully published.
        :param data:
        :return:
        """
        sn_event_id = data['vendor_event_id']
        social_network_id = data['social_network_id']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(
            self.user_id,
            social_network_id,
            sn_event_id
        )
        try:
            if event:
                event.update(**data)
                # TODO we shouldn't commit here
                Event.session.commit()
            else:
                event = Event(**data)
                Event.save(event)
        except Exception as e:
            error_message = 'Event was not saved in Database\nError: %s' % e.message
            log_error({
                            'Reason':error_message,
                            'functionName': 'save_event',
                            'fileName': __file__,
                            'User': self.user.id
                        })
            raise EventNotSaveInDb('Error occurred while saving event in databse')

        return event.id

    def event_sn_to_gt_mapping(self, *args, **kwargs):
        pass

    def event_gt_to_sn_mapping(self, *args, **kwargs):
        pass
