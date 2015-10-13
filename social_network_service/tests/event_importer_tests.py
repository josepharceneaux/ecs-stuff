# Application Specific
from common.models.event import Event
from common.models.user import UserCredentials
from social_network_service.meetup import Meetup


class Test_Event_Importer():

    def test_meetup_event(self, test_user, auth_data, event_in_db):
        event_social_network_id = event_in_db.social_network.id
        user_credentials = UserCredentials.get_by_user_and_social_network_id(test_user.id,
                                                                             event_in_db.social_network.id)
        Event.delete(event_in_db.id)
        sn = Meetup(user_id=test_user.id)
        sn.process('event', user_credentials=user_credentials)
        event = Event.get_by_user_and_social_network_event_id(test_user.id,
                                                              event_social_network_id)
        assert event.description.find("Test Event Description")
