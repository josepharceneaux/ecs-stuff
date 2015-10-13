# Application Specific
from common.models.event import Event
from common.models.rsvp import RSVP
from common.models.user import UserCredentials
from common.models.social_network import SocialNetwork
from social_network_service.utilities import get_class, http_request


class Test_Event_Importer():
    """
    This is the test of event importer both for Meetup and Eventbrite.
    We first call process_event() to create event on social network website
    and save it in database. After this we delete this event from database
    and import all the events of test user created by fixture.
    Then we assert if newly created event has been imported or not.
    """
    def test_meetup_event(self, auth_data, meetup_event):
        """
        This test uses fixtures
        'auth_data' to create user credentials and
        'meetup_event' to create events on Meetup websites.
        """
        social_network_event_id = meetup_event.social_network_event_id
        user_credentials = UserCredentials.get_by_user_and_social_network_id(
            auth_data['user_id'], meetup_event.social_network.id)
        Event.delete(meetup_event.id)
        # create object of respective social network
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token
        sn = social_network_class(user_id=user_credentials.user_id)
        sn.process('event', user_credentials=user_credentials)
        event = Event.get_by_user_and_social_network_event_id(auth_data['user_id'],
                                                              social_network_event_id)
        assert event.description.find("Test Event Description")

    def test_meetup_rsvp(self, auth_data, meetup_event):
        """
        This test uses fixtures
        'auth_data' to create user credentials and
        'meetup_event' to create events on Meetup websites.

        - Here we use fixture meetup_event to create new event on Meetup
            website. After success we post an RSVP on this event.
            We assert on response of RSVP POST. If it is in 2xx, then we run
            rsvp importer to import RSVP (that we just posted) in database.
            After importing RSVPs, we pick the imported record
            using social_network_rsvp_id and finally assert on the status of
            RSVP. It should be same as given in POST request's payload.
        """

        social_network_event_id = meetup_event.social_network_event_id
        user_credentials = UserCredentials.get_by_user_and_social_network_id(
            auth_data['user_id'], meetup_event.social_network.id)
        # create object of respective social network
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token
        sn = social_network_class(user_id=user_credentials.user_id)
        url = sn.api_url + '/rsvp/'
        payload = {'event_id': social_network_event_id,
                   'rsvp': 'no'}
        response = http_request('POST', url, params=payload, headers=sn.headers)
        assert response.ok is True
        social_network_rsvp_id = response.json()['rsvp_id']
        sn.process('rsvp', user_credentials=user_credentials)
        rsvp_in_db = RSVP.get_by_social_network_rsvp_id_and_social_network_id(
            social_network_rsvp_id, social_network.id)
        assert rsvp_in_db.status == payload['rsvp']
