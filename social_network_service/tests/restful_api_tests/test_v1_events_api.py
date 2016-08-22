"""
This file contain tests for events api
"""
# Std imports
import sys
import json

# Third-Part imports
import pytest
import requests
from requests import codes

# App specific imports
from social_network_service.common.models import db
from social_network_service.social_network_app import logger
from social_network_service.common.models.misc import Activity
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.tests.helper_functions import auth_header, send_post_request
from social_network_service.common.campaign_services.tests_helpers import assert_invalid_datetime_format
from social_network_service.custom_exceptions import (VenueNotFound, EventInputMissing, EventOrganizerNotFound,
                                                      SocialNetworkNotImplemented, SocialNetworkError)


class TestResourceEvents(object):
    def test_get_with_invalid_token(self):
        """
        - Try to get events using invalid access_token.
        - Expect 401 (unauthorized) in response
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_event_get_with_valid_token(self, auth_token):
        """
        - Get events using valid access_token
        - As the test user is newly created. so, initially there will be no events
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(auth_token))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) == 0, 'There shouldn\'t be some events for test user'

    def test_events_get_with_valid_token(self, token_first, event_in_db):
        """
        event_in_db fixture creates an event entry in db. So, when request is made, it should return that created event
        for test user
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) >= 1, 'There should be some events for test user'

    def test_events_post_with_invalid_token(self):
        """
        Post event using invalid token and response should be 401 (unauthorized user)
        """
        response = send_post_request(SocialNetworkApiUrl.EVENTS, {}, 'invalid_token')
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_events_post_with_invalid_social_network_id(self, token_first, test_event):
        """
        Post event using invalid social_network_id i.e equal to -1. response should be 500 with 4052 error code
        (Social Network not found)
        """
        event_data = test_event

        # test with a social network that does not exists
        event_data['social_network_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.INTERNAL_SERVER_ERROR
        response = response.json()
        assert 'error' in response and response['error']['code'] == SocialNetworkError.error_code, \
            'Social Network not found'

    def test_events_post_no_event_implementation(self, token_first, test_event):
        """
        Post event using invalid social_network_id i.e equal to 1. response should be 500 with 4062 error code
        (Social Network have no events implementations)
        """
        event_data = test_event

        # test social network which have no implementation for events
        event_data['social_network_id'] = 1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.INTERNAL_SERVER_ERROR
        response = response.json()

        assert 'error' in response and response['error']['code'] == SocialNetworkNotImplemented.error_code, \
            'Social Network have no events implementation'

    def test_events_post_no_event_organizer(self, token_first, test_event):
        """
        Post event using invalid event_organizer i.e equal to -1. response should be 500 with 4054 error code
        (Event organizer not found)
            url -> localhost:8007/v1/events
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        event_data['social_network_id'] = social_network_id
        social_network = SocialNetwork.get_by_id(social_network_id)

        # test with invalid organizer
        event_data['organizer_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        if social_network.name.lower() == 'meetup':
            assert response.status_code == codes.BAD_REQUEST, response.text
            return
        else:
            assert response.status_code == codes.NOT_FOUND, response.text
        response = response.json()

        assert 'error' in response and response['error']['code'] == EventOrganizerNotFound.error_code, \
            'Event organizer not found'

    def test_events_post_no_venue(self, token_first, test_event):
        """
        Post event using invalid venue_id i.e equal to -1. response should be 404 with 4065 error code
        (Venue not found)
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        event_data['social_network_id'] = social_network_id

        # test with invalid venue
        event_data['venue_id'] = sys.maxint
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.NOT_FOUND
        response = response.json()
        assert 'error' in response and response['error']['code'] == VenueNotFound.error_code, 'Venue not found'

    def test_events_post_invalid_datetime_format(self, token_first, test_event):
        """
        Post event using invalid start_datetime format. Response should be 400.
        Valid format is "%Y-%m-%dT%H:%M:%S.%fZ".
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        venue_id = event_data['venue_id']
        event_data['social_network_id'] = social_network_id
        event_data['venue_id'] = venue_id
        # Now test with invalid start datetime UTC format
        assert_invalid_datetime_format('post', SocialNetworkApiUrl.EVENTS, token_first, event_data.copu(),
                                       'start_datetime')
        assert_invalid_datetime_format('post', SocialNetworkApiUrl.EVENTS, token_first, event_data, 'end_datetime')

    def test_events_post_with_valid_token(self, token_first, test_event):
        """
        Post event and it should create an event with 201 response
        """
        event_data = test_event

        # Success case
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.CREATED, 'Status should be Ok, Resource Created (201)'
        event_id = response.json()['id']
        db.db.session.commit()
        activities = Activity.get_by_user_id_type_source_id(user_id=event_data['user_id'],
                                                            source_id=event_id,
                                                            type_=Activity.MessageIds.EVENT_CREATE)
        data = json.loads(activities.params)
        assert data['event_title'] == event_data['title']

        assert event_id > 0, 'Event id should be a positive number'
        test_event['id'] = event_id  # Add created event id  in test_event so it can be deleted in tear_down

    def test_eventbrite_with_missing_required_fields(self, token_first, eventbrite_missing_data,
                                                     test_eventbrite_credentials):
        """
        Post event data with missing required keys and response should be 400 (4053 - Missing Keys)
        """
        key, event_data = eventbrite_missing_data
        event_data[key] = ''
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.BAD, 'It should fail'
        response = response.json()
        assert response['error']['code'] == EventInputMissing.error_code, \
            'There should be an missing field error for %s KeyError' % key

    @pytest.mark.skipif(True, reason='TODO: Modify following tests when meetup sandbox testing issue is resolved')
    def test_meetup_with_valid_address(self, token_first, meetup_event_data, test_meetup_credentials):
        """
        Send Post request with meetup_event data and response should be 201 (event created)
        """
        event_data = meetup_event_data
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.CREATED, 'Event should be created, address is valid'
        event_id = response.json()['id']
        meetup_event_data['id'] = event_id

    @pytest.mark.skipif(True, reason='TODO: Modify following tests when meetup sandbox testing issue is resolved')
    def test_meetup_with_invalid_address(self, token_first, meetup_event_data, test_meetup_credentials):
        """
        Send post request with invalid meetup_event data (change venue_id) and response should be 404 with error code
        4065 (Address invalid)
        """
        event_data = meetup_event_data
        event_data['venue_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token_first)
        logger.info(response.text)
        assert response.status_code == codes.NOT_FOUND, 'Venue not Found in database'
