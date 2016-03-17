"""
This file contain tests for events api
"""

# Std imports
import datetime

# Third-Part imports
import json

import requests

# App specific imports
import sys

from social_network_service.common.models import db
from social_network_service.common.models.misc import Activity
from social_network_service.custom_exceptions import VenueNotFound, \
    EventInputMissing, InvalidDatetime, EventOrganizerNotFound, SocialNetworkNotImplemented, SocialNetworkError
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.tests.helper_functions import auth_header, send_post_request


class TestResourceEvents:

    def test_get_with_invalid_token(self):
        """
        - Try to get events using invalid access_token.
        - Expect 401 (unauthorized) in response
        :return:
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS,
                                headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_event_get_with_valid_token(self, token):
        """
        - Get events using valid access_token
        - As the test user is newly created. so, initially there will be no events
        :param token:
        :return:
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS,
                                headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) == 0, 'There should be some events for test user'

    def test_events_get_with_valid_token(self, token, event_in_db):
        """
        event_in_db fixture creates an event entry in db. So, when request is made, it should return that created event
        for test user
        :param token: access_token for oauth
        :param event_in_db: fixture to create event in db
        :return:
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) > 1, 'There should be some events for test user'

    def test_events_post_with_invalid_token(self):
        """
        Post event using invalid token and response should be 401 (unauthorized user)
        :return:
        """
        response = send_post_request(SocialNetworkApiUrl.EVENTS, {}, 'invalid_token')
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_events_post_with_invalid_social_network_id(self, token, test_event):
        """
        Post event using invalid social_network_id i.e equal to -1. response should be 500 with 4052 error code
        (Social Network not found)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event

        # test with a social network that does not exists
        event_data['social_network_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == SocialNetworkError.error_code, 'Social Network not found'

    def test_events_post_no_event_implementation(self, token, test_event):
        """
        Post event using invalid social_network_id i.e equal to 1. response should be 500 with 4062 error code
        (Social Network have no events implementations)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event

        # test social network which have no implementation for events
        event_data['social_network_id'] = 1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()

        assert 'error' in response and response['error']['code'] == SocialNetworkNotImplemented.error_code, \
            'Social Network have no events implementation'

    def test_events_post_no_event_organizer(self, token, test_event):
        """
        Post event using invalid event_organizer i.e equal to -1. response should be 500 with 4054 error code
        (Event organizer not found)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        event_data['social_network_id'] = social_network_id

        # test with invalid organizer
        event_data['organizer_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 404
        response = response.json()

        assert 'error' in response and response['error']['code'] == EventOrganizerNotFound.error_code, \
            'Event organizer not found'

    def test_events_post_no_venue(self, token, test_event):
        """
        Post event using invalid venue_id i.e equal to -1. response should be 500 with 4065 error code
        (Venue not found)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        organizer_id = event_data['organizer_id']

        event_data['social_network_id'] = social_network_id
        event_data['organizer_id'] = organizer_id

        # test with invalid venue
        event_data['venue_id'] = sys.maxint
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 404
        response = response.json()
        assert 'error' in response and response['error']['code'] == VenueNotFound.error_code, 'Venue not found'

    def test_events_post_invalid_start_datetime(self, token, test_event):
        """
        Post event using invalid start_datetime format. response should be 500 with 4064 error code
        (Social Network not found)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        organizer_id = event_data['organizer_id']
        venue_id = event_data['venue_id']

        event_data['social_network_id'] = social_network_id
        event_data['organizer_id'] = organizer_id

        event_data['venue_id'] = venue_id
        # TODO in this and the following test comment what exactly makes teh date valid OR what valid date looks like
        # Now test with invalid start datetime UTC format
        datetime_now = datetime.datetime.now()
        event_data['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%S')
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 400
        response = response.json()
        # TODO break the line
        assert 'error' in response and response['error']['code'] == InvalidDatetime.error_code, 'Invalid start datetime format'

    def test_events_post_invalid_end_datetime(self, token, test_event):
        """
        Post event using invalid end_datetime format. response should be 500 with 4064 error code
        (Social Network not found)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        organizer_id = event_data['organizer_id']
        venue_id = event_data['venue_id']

        event_data['social_network_id'] = social_network_id
        event_data['organizer_id'] = organizer_id

        event_data['venue_id'] = venue_id

        # Now test with invalid start datetime UTC format
        datetime_now = datetime.datetime.now()
        event_data['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
        event_data['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S')
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 400
        response = response.json()
        assert 'error' in response and response['error']['code'] == InvalidDatetime.error_code, 'Invalid end datetime format'
        event_data['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')

    def test_events_post_with_valid_token(self, token, test_event):
        """
        Post event and it should create an event with 201 response
        (Scoail Network not found)
        :param token: access_token for oauth
        :param test_event: test_event for post a valid event data
        :return:
        """
        event_data = test_event

        # Success case
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 201, 'Status should be Ok, Resource Created (201)'
        event_id = response.json()['id']
        db.db.session.commit()
        activities = Activity.get_by_user_id_type_source_id(user_id=event_data['user_id'],
                                                            source_id=event_id,
                                                            type_=Activity.MessageIds.EVENT_CREATE)
        data = json.loads(activities.params)
        assert data['event_title'] == event_data['title']

        assert event_id > 0, 'Event id should be a positive number'
        test_event['id'] = event_id     # Add created event id  in test_event so it can be deleted in tear_down

    def test_eventbrite_with_missing_required_fields(self, token, eventbrite_missing_data,
                                                     test_eventbrite_credentials):
        """
        Post event data with missing required keys and response should be 500 (4053 - Missing Keys)
        :param token: accesstoken
        :param eventbrite_missing_data: eventbrite data fixture
        :param test_eventbrite_credentials:
        :return:
        """
        key, event_data = eventbrite_missing_data
        event_data[key] = ''
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 400, 'It should fail'
        response = response.json()
        assert response['error']['code'] == EventInputMissing.error_code, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_missing_required_fields(self, token, meetup_missing_data, test_meetup_credentials):
        """
        Post meetup data with missing required keys and response should be 500 with 4053 error code (Missing Field)
        :param token:
        :param meetup_missing_data:
        :param test_meetup_credentials:
        :return:
        """
        key, event_data = meetup_missing_data
        event_data[key] = ''
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        #TODO assert message sohuld be more clear e.g. "Couldn't create event because required fields were missing"
        assert response.status_code == 400, 'It should fail'
        response = response.json()
        assert response['error']['code'] == EventInputMissing.error_code, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_valid_address(self, token, meetup_event_data, test_meetup_credentials):
        """
        Send Post request with meetup_event data and response should be 201 (event created)
        :param token: oauth access_token
        :param meetup_event_data: test meetup data
        :param test_meetup_credentials:
        :return:
        """
        event_data = meetup_event_data
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 201, 'Event should be created, address is valid'
        event_id = response.json()['id']
        meetup_event_data['id'] = event_id

    def test_meetup_with_invalid_address(self, token, meetup_event_data, test_meetup_credentials):
        """
        Send post request with invalid meetup_event data (change venue_id) and response should be 500 with error code
        4065 (Address invalid)
        :param token:
        :param meetup_event_data:
        :param test_meetup_credentials:
        :return:
        """
        event_data = meetup_event_data
        event_data['venue_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 404, 'Venue not Found in database'
        response = response.json()
        assert response['error']['code'] == VenueNotFound.error_code, \
            'Event should not be created, address is invalid according to Meetup API'


