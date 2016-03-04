# Application Specific
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.event import Event
from social_network_service.common.models.rsvp import RSVP
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.utilities import get_class
from social_network_service.social_network_app import logger


class Test_Event_Importer:
    """
    - This class contains tests for both event importer and RSVP importer for
    Meetup. We use fixtures
     1- auth_data to create test user and its credentials
     2- meetup_event_dict to create event on social network website and put
        it in dict.
    """
    def test_meetup_event_importer_with_invalid_token(self, sample_user,
                                                      meetup_event_dict):
        """
        :param auth_data: This creates a test user and its social network
            credentials.
        :param meetup_event_dict: This creates an event on social network website
            and saves it in database.
        :type auth_data: pyTest fixture present in conftest.py.
        :type meetup_event_dict: pyTest fixture present in conftest.py.

        - At first we delete this event from database and run importer with
            invalid token. Then we assert that newly created event has not been
            imported. We add 'id' of imported event to delete newly created
            event from social network website in the finalizer of
            meetup_event_dict.
        """
        event = meetup_event_dict['event']
        meetup_event_dict['id'] = event.id
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            sample_user.id, event.social_network.id)
        Event.delete(event.id)
        # create object of respective social network to run Event importer
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token to make HTTP calls
        sn = social_network_class(user_id=user_credentials.user_id)
        sn.headers = {'Authorization': 'Bearer invalid_token'}
        logger.debug('Access Token has been malformed.')
        sn.process('event', user_credentials=user_credentials)
        # get the imported event by social_network_event_id and user_id
        event = Event.get_by_user_and_social_network_event_id(sample_user.id,
                                                              social_network_event_id)
        assert event is None

    def test_meetup_event_importer_with_valid_token(self, sample_user, meetup_event_dict):
        """
        :param auth_data: This creates a test user and its social network
            credentials.
        :param meetup_event_dict: This creates an event on social network website
            and saves it in database.
        :type auth_data: pyTest fixture present in conftest.py.
        :type meetup_event_dict: pyTest fixture present in conftest.py.

        - First of all we delete this event from database and import all the
            events of test user created by fixture. Then we assert if newly
            created event has been imported or not. We add 'id' of imported
            event to delete newly created event from social network website in
            the finalizer of meetup_event_dict.
        """
        event = meetup_event_dict['event']
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            sample_user.id, event.social_network.id)
        Event.delete(event.id)
        # create object of respective social network to run Event importer
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token to make HTTP calls
        sn = social_network_class(user_id=user_credentials.user_id)
        sn.process('event', user_credentials=user_credentials)
        # get the imported event by social_network_event_id and user_id
        event = Event.get_by_user_and_social_network_event_id(
            sample_user.id, social_network_event_id)
        assert isinstance(event, Event), "event should be a model object"
        assert event.description.find("Test Event Description"), \
            'Event not imported in database'
        meetup_event_dict['id'] = event.id

    def test_meetup_rsvp_importer_with_invalid_token(self, sample_user,
                                                     meetup_event_dict):
        """
        :param auth_data: This creates a test user and its social network
            credentials.
        :param meetup_event_dict: This creates an event on social network website
            and saves it in database.
        :type auth_data: pyTest fixture present in conftest.py.
        :type meetup_event_dict: pyTest fixture present in conftest.py.

        - Here we post an RSVP on newly created event and assert on response
            of RSVP POST. It should be 2xx, then we run rsvp importer with
            invalid token. RSVP for this event should not be imported.
        - We add 'id' of newly created event to delete it from social network
            website in the finalizer of meetup_event_dict.
        """
        event = meetup_event_dict['event']
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            sample_user.id, event.social_network.id)
        # create object of respective social network to run RSVP importer
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token to make HTTP calls
        sn = social_network_class(user_id=user_credentials.user_id)
        url = sn.api_url + '/rsvp/'
        payload = {'event_id': social_network_event_id,
                   'rsvp': 'no'}
        response = http_request('POST', url, params=payload, headers=sn.headers)
        assert response.ok is True
        logger.debug('RSVP has been posted successfully')
        social_network_rsvp_id = response.json()['rsvp_id']
        sn.headers = {'Authorization': 'Bearer invalid_token'}
        logger.debug('Access Token has been malformed.')
        sn.process('rsvp', user_credentials=user_credentials)
        # get the imported RSVP by social_network_rsvp_id and social_network_id
        rsvp_in_db = RSVP.get_by_social_network_rsvp_id_and_social_network_id(
            social_network_rsvp_id, social_network.id)
        assert rsvp_in_db is None
        meetup_event_dict['id'] = event.id

    def test_meetup_rsvp_importer_with_valid_token(self, sample_user, meetup_event_dict):
        """
        :param auth_data: This creates a test user and its social network
            credentials.
        :param meetup_event_dict: This creates an event on social network website
            and saves it in database.
        :type auth_data: pyTest fixture present in conftest.py.
        :type meetup_event_dict: pyTest fixture present in conftest.py.

        - We post an RSVP on this event. We assert on response of RSVP POST.
            If it is in 2xx, then we run rsvp importer to import RSVP
            (that we just posted) in database. After importing RSVPs, we pick
            the imported record using social_network_rsvp_id and finally assert
            on the status of RSVP. It should be same as given in POST request's
            payload.

        - We add 'id' of newly created event to delete it from social network
            website in the finalizer of meetup_event_dict.
        """
        event = meetup_event_dict['event']
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            sample_user.id, event.social_network.id)
        # create object of respective social network to run RSVP importer
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token to make HTTP calls
        sn = social_network_class(user_id=user_credentials.user_id)
        url = sn.api_url + '/rsvp/'
        payload = {'event_id': social_network_event_id,
                   'rsvp': 'no'}
        response = http_request('POST', url, params=payload, headers=sn.headers)
        assert response.ok is True
        logger.debug('RSVP has been posted successfully')
        social_network_rsvp_id = response.json()['rsvp_id']
        sn.process('rsvp', user_credentials=user_credentials)
        # get the imported RSVP by social_network_rsvp_id and social_network_id
        rsvp_in_db = RSVP.get_by_social_network_rsvp_id_and_social_network_id(
            social_network_rsvp_id, social_network.id)
        assert isinstance(rsvp_in_db, RSVP)
        assert rsvp_in_db.status == payload['rsvp']
        meetup_event_dict['id'] = event.id
