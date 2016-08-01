# Std imports
import json
from time import sleep
import requests
from datetime import datetime

# Application Specific
from social_network_service.common.models import db
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.event import Event
from social_network_service.common.models.rsvp import RSVP
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.routes import SocialNetworkApiUrl
# TODO: I think no need to import these
from social_network_service.common.tests.api_conftest import user_first, token_first, talent_pool
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.utilities import get_class
from social_network_service.social_network_app import logger
from social_network_service.common.utils.handy_functions import send_request

# TODO: Do we have a test where user has no talent-pool?
# TODO: Do we have a test where we run importer more than once and assert that only one entry saves in DB, respective tables?
class Test_Event_Importer:
    """
    - This class contains tests for both event importer and RSVP importer for
    Meetup. We use fixtures
     1- auth_data to create test user and its credentials
     2- meetup_event_dict to create event on social network website and put
        it in dict.
    """
    def test_meetup_event_importer_with_invalid_token(self, user_first,
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
        # TODO: I think docs are not correct
        event = meetup_event_dict['event']
        meetup_event_dict['id'] = event.id
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            user_first['id'], event.social_network.id)
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
        event = Event.get_by_user_and_social_network_event_id(user_first['id'],
                                                              social_network_event_id)
        assert event is None

    def test_meetup_event_importer_with_valid_token(self, user_first, meetup_event_dict, talent_pool,
                                                    meetup_event_data, token_first):
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
        # TODO: I think docs are not correct
        event = meetup_event_dict['event']
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            user_first['id'], event.social_network.id)
        Event.delete(event.id)
        # create object of respective social network to run Event importer
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network',
                                         user_credentials=user_credentials)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token to make HTTP calls
        sn = social_network_class(user_id=user_credentials.user_id)
        sn.process('event', user_credentials=user_credentials)
        db.db.session.commit()
        # get the imported event by social_network_event_id and user_id
        event = Event.get_by_user_and_social_network_event_id(
            user_first['id'], social_network_event_id)
        assert isinstance(event, Event), "event should be a model object"
        assert event.description.find("Test Event Description"), \
            'Event not imported in database'

        response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event.id,
                                access_token=token_first)

        assert response.status_code == 200

    def test_meetup_rsvp_importer_with_invalid_token(self, user_first, token_first,
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
            user_first['id'], event.social_network.id)
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
        # TODO: I think print will be helpful in terms of jenkins
        logger.debug('RSVP has been posted successfully')
        social_network_rsvp_id = response.json()['rsvp_id']
        sn.headers = {'Authorization': 'Bearer invalid_token'}
        logger.debug('Access Token has been malformed.')
        sn.process('rsvp', user_credentials=user_credentials)
        # get the imported RSVP by social_network_rsvp_id and social_network_id
        rsvp_in_db = RSVP.get_by_social_network_rsvp_id_and_social_network_id(
            social_network_rsvp_id, social_network.id)
        assert rsvp_in_db is None
        response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event.id,
                                access_token=token_first)

        assert response.status_code == 200

    def test_meetup_rsvp_importer_with_valid_token(self, user_first, token_first, meetup_event_dict):
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
        # TODO: Outdated docs w.r.t params: Applies to more than one places
        event = meetup_event_dict['event']
        social_network_event_id = event.social_network_event_id
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            user_first['id'], event.social_network.id)
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
        response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event.id,
                                access_token=token_first)

        assert response.status_code == 200

    def test_meetup_rsvp_importer_endpoint_with_valid_token(self, user_first, talent_pool,
                                                            meetup_event_dict,
                                                            token_first):
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
        # TODO: Didn't understand difference between this and test_meetup_rsvp_importer_with_valid_token()?
        headers = dict(Authorization='Bearer %s' % token_first)
        headers['Content-Type'] = 'application/json'
        response = requests.post(url=SocialNetworkApiUrl.IMPORTER % ('rsvp', 'meetup'), headers=headers)
        assert response.status_code == 200

    def test_eventbrite_event_importer_endpoint(self, token_first):
        """
        Test Eventbrite events importer.
        - An existing event is created on eventbrite with id `26557579435` and is associated with our user id 1
        - Run event importer for eventbrite.
        - Then check if event event is imported correctly or not
        """
        social_network_event_id = '26557579435'
        user_id = 1  # TODO: Why 1? why not user_first fixture?
        event = Event.get_by_user_and_social_network_event_id(user_id=user_id,
                                                              social_network_event_id=social_network_event_id)

        social_network = SocialNetwork.get_by_name('Eventbrite')

        user_credential = UserSocialNetworkCredential.get_by_user_and_social_network_id(user_id, social_network.id)
        assert user_credential
        # Change the last updated time to past and run importer. After that check if event is imported.
        user_credential.update(last_updated=datetime(2012, 12, 1))
        if event:
            Event.delete(event)
        headers = dict(Authorization='Bearer %s' % token_first)
        headers['Content-Type'] = 'application/json'

        response = requests.post(url=SocialNetworkApiUrl.IMPORTER % ('event', 'eventbrite'),
                                 headers=headers)
        assert response.status_code == 200
        sleep(80)  # TODO: See if we can do polling here: Applies to more than one places
        db.db.session.commit()
        event = Event.get_by_user_and_social_network_event_id(user_id=user_id,
                                                              social_network_event_id=social_network_event_id)
        assert event

        Event.delete(event.id) # TODO: Why not delete from API endpoint?

    def test_eventbrite_rsvp_importer_endpoint(self, token_first):
        """
        Test eventbrite rsvps importer.
        A pre-existing rsvp is on eventbrite.
        - Run rsvp importer for eventbrite.
        - Then check if already created rsvp is imported correctly or not
        """

        rsvp_id = '672393772'
        social_network_event_id = '26557579435'
        user_id = 1
        headers = dict(Authorization='Bearer %s' % token_first)
        headers['Content-Type'] = 'application/json'

        eventbrite_obj = SocialNetwork.get_by_name('Eventbrite')

        rsvp = RSVP.get_by_social_network_rsvp_id_and_social_network_id(rsvp_id, eventbrite_obj.id)

        if rsvp:
            RSVP.delete(rsvp.id)

        event = Event.get_by_user_and_social_network_event_id(
            user_id=user_id, social_network_event_id=social_network_event_id)
        # If event is not imported then run event importer and import events first
        if not event:
            # Import events first then import RSVPs
            response = requests.post(url=SocialNetworkApiUrl.IMPORTER % ('event', 'eventbrite'),
                                     headers=headers)
            assert response.status_code == 200

            sleep(50)

        response = requests.post(url=SocialNetworkApiUrl.IMPORTER % ('rsvp', 'eventbrite'), data=json.dumps({}),
                                 headers=headers)
        assert response.status_code == 200
        sleep(80)
        db.db.session.commit()
        rsvp = RSVP.get_by_social_network_rsvp_id_and_social_network_id(rsvp_id, eventbrite_obj.id)
        assert rsvp

    def test_meetup_event_importer_endpoint(self, user_first, meetup_event, meetup_event_dict, token_first):
        """
        Test meetup events importer.
        - Create an event on meetup using social network service endpoint
        - Then delete meetup event directly from db
        - Then run event importer for meetup.
        - Then check if event event is imported correctly or not
        """
        event = meetup_event_dict['event']
        social_network_event_id = event.social_network_event_id
        Event.delete(event.id)

        social_network = SocialNetwork.get_by_name('Meetup')

        user_credential = UserSocialNetworkCredential.get_by_user_and_social_network_id(user_first['id'],
                                                                                        social_network.id)
        assert user_credential
        # Change the last updated time to past and run importer. After that check if event is imported.
        user_credential.update(last_updated=datetime(2012, 12, 1))
        headers = dict(Authorization='Bearer %s' % token_first)
        headers['Content-Type'] = 'application/json'

        response = requests.post(url=SocialNetworkApiUrl.IMPORTER % ('event', 'meetup'),headers=headers)
        assert response.status_code == 200
        sleep(80)
        event = Event.get_by_user_and_social_network_event_id(user_first['id'],
                                                              social_network_event_id=social_network_event_id)
        db.db.session.commit()
        assert event
