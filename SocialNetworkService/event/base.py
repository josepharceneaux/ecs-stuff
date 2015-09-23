from gt_common.gt_models.event import Event
from gt_common.gt_models.user import User
from gt_common.gt_models.user import UserCredentials
from gt_common.gt_models.social_network import SocialNetwork

class EventBase(object):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user') or None
        self.social_network = kwargs.get('social_network') or None
        assert isinstance(self.user, User)
        assert isinstance(self.social_network, SocialNetwork)
        self.api_url = self.social_network.apiUrl
        self.member_id, self.access_token, self.refresh_token, self.webhook = \
            self._get_user_credentials()

    def _get_user_credentials(self):
        user_credentials = UserCredentials.get_by_user_and_social_network(
            self.user.id, self.social_network.id
        )
        assert user_credentials is not None
        member_id = user_credentials.memberId
        access_token = user_credentials.accessToken
        refresh_token = user_credentials.refreshToken
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
        self.pre_process_events(events)
        for event in events:
            print 'Normalize'
            event = self.normalize_event(event)
            print 'Normalized'
            print event
            if event:
                event_in_db = Event.get_by_user_and_vendor_id(event.userId,
                                                              event.vendorEventId)
                print 'Event in db', event_in_db
                if event_in_db:
                    data = dict(eventTitle=event.eventTitle,
                                eventDescription=event.eventDescription,
                                eventAddressLine1=event.eventAddressLine1,
                                eventStartDateTime=event.eventStartDateTime,
                                eventEndDateTime=event.eventEndDateTime)
                    event_in_db.update(**data)
                else:
                    Event.save(event)
        self.post_process_events(events)

    def post_process_events(self, events):
        pass
