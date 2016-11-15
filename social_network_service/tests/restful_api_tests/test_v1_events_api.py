"""
This file contain tests for events api
"""
# Std imports
import sys
import json
import time

# Third-Part imports
import requests
from datetime import datetime, timedelta
from requests import codes

# App specific imports
from social_network_service.common.models import db
from social_network_service.common.constants import MEETUP
from social_network_service.common.tests.conftest import fake
from social_network_service.common.utils.datetime_utils import DatetimeUtils
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

    def test_event_get_with_valid_token(self, token_second):
        """
        - Get events using valid access_token
        - As the test user is newly created. so, initially there will be no events
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(token_second))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) == 0, 'There shouldn\'t be some events for test user'

    def test_events_get_with_valid_token(self, token_first, event_in_db_second):
        """
        event_in_db fixture creates an event entry in db. So, when request is made, it should return that created event
        for test user
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) >= 1, 'There should be some events for test user'

    def test_events_get_in_domain_of_user(self, token_same_domain, event_in_db, event_in_db_second):
        """
        Here one user tries to get events in its domain. It should get 2 events created by some other user of
        same domain.
        """
        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(token_same_domain))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) >= 2, 'There should be 2 events for user of same domain'

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
        Post event using invalid event_organizer i.e equal to -1. response should be 201
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
        if social_network.name.lower() == MEETUP:
            assert response.status_code == codes.BAD_REQUEST, "Response: {}".format(response.text)
            return
        else:
            assert response.status_code == codes.CREATED, "Response: {}".format(response.text)

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
        Post event using invalid start_datetime and start_datetime formats. Response should be 400.
        Valid format is "%Y-%m-%dT%H:%M:%S.%fZ".
        """
        event_data = test_event
        social_network_id = event_data['social_network_id']
        venue_id = event_data['venue_id']
        event_data['social_network_id'] = social_network_id
        event_data['venue_id'] = venue_id
        # Now test with invalid start datetime UTC format
        assert_invalid_datetime_format('post', SocialNetworkApiUrl.EVENTS, token_first, event_data.copy(),
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

    # def test_events_get_with_query(self, token_first, token_same_domain, user_first, user_same_domain,
    #                                eventbrite_event_data, meetup, eventbrite, eventbrite_venue_same_domain,
    #                                test_eventbrite_credentials_same_domain):
    #     """
    #     In this test, we will create three events, two for user_first, one for user_same_domain.
    #     Then we will try all search and filter options.
    #     """
    #     title = fake.sentence() + str(datetime.now())
    #     title_first = 'ABC' + title
    #     title_second = 'XYZ' + title
    #     title_third = 'DEF' + title
    #     start_datetime_first = (datetime.now() + timedelta(days=5)).replace(microsecond=0)
    #     start_datetime_second = (datetime.now() + timedelta(days=10)).replace(microsecond=0)
    #     start_datetime_third = (datetime.now() + timedelta(days=15)).replace(microsecond=0)
    #     create_event(token_first, eventbrite_event_data, title_first, start_datetime_first)
    #     create_event(token_first, eventbrite_event_data, title_second, start_datetime_second)
    #     eventbrite_event_data['venue_id'] = eventbrite_venue_same_domain['id']
    #     create_event(token_same_domain, eventbrite_event_data, title_third, start_datetime_third)
    #
    #     events = get_events_with_query(token_first)
    #     assert len(events) == 3
    #     events = get_events_with_query(token_first, search=title)
    #     assert len(events) == 3
    #     for search in [title_first, title_second, title_third]:
    #         events = get_events_with_query(token_first, search=search)
    #         assert len(events) == 1, 'Expected: %s, Actual: %s, search: %s' % (1, len(events), search)
    #     events = get_events_with_query(token_first, search=fake.sentence())
    #     assert len(events) == 0
    #     events = get_events_with_query(token_first, sort_by='title', sort_type='asc')
    #     assert len(events) == 3
    #     for index, search in enumerate([title_first, title_third, title_second]):
    #         assert events[index]['title'] == search, 'Expected: %s, Actual: %s, search: %s' % (search,
    #                                                                                            events[index]['title'],
    #                                                                                            search)
    #     events = get_events_with_query(token_first, sort_by='title', sort_type='desc')
    #     assert len(events) == 3
    #     for index, search in enumerate([title_second, title_third, title_first]):
    #         assert events[index]['title'] == search
    #
    #     events = get_events_with_query(token_first, sort_by='start_datetime')
    #     events_desc = get_events_with_query(token_first, sort_by='start_datetime', sort_type='desc')
    #     assert len(events) == 3
    #     assert len(events_desc) == 3
    #     assert events == events_desc
    #     for index, date in enumerate([start_datetime_third, start_datetime_second, start_datetime_first]):
    #         assert events[index]['start_datetime'] == date.strftime("%Y-%m-%d %H:%M:%S")
    #
    #     events = get_events_with_query(token_first, sort_by='start_datetime', sort_type='asc')
    #     assert len(events) == 3
    #     events_desc.reverse()
    #     assert events_desc == events
    #     for index, date in enumerate([start_datetime_first, start_datetime_second, start_datetime_third]):
    #         assert events[index]['start_datetime'] == date.strftime("%Y-%m-%d %H:%M:%S")
    #
    #     events = get_events_with_query(token_first, user_id=user_first['id'])
    #     assert len(events) == 2
    #
    #     events = get_events_with_query(token_first, user_id=user_same_domain['id'])
    #     assert len(events) == 1
    #
    #     events = get_events_with_query(token_first, social_network_id=eventbrite['id'])
    #     assert len(events) == 3
    #     events = get_events_with_query(token_first, social_network_id=meetup['id'])
    #     assert len(events) == 0


def get_events_with_query(token, search=None, social_network_id=None,  sort_by=None, sort_type=None, user_id=None):
    url = SocialNetworkApiUrl.EVENTS
    if search:
        url += '?search=%s' % search
    if social_network_id:
        url += '?social_network_id=%s' % social_network_id if url.find('?') == -1 \
            else '&social_network_id=%s' % social_network_id
    if sort_by:
        url += '?sort_by=%s' % sort_by if url.find('?') == -1 else '&sort_by=%s' % sort_by
    if sort_type:
        url += '?sort_type=%s' % sort_type if url.find('?') == -1 else '&sort_type=%s' % sort_type
    if user_id:
        url += '?user_id=%s' % user_id if url.find('?') == -1 else '&user_id=%s' % user_id
    response = requests.get(url, headers=auth_header(token))
    logger.info(response.text)
    assert response.status_code == codes.OK, 'Status should be Ok (200)'
    return response.json()['events']


def create_event(token, event_data, title, start_datetime):
    end_datetime = start_datetime + timedelta(hours=3)
    data = dict(
        title=title,
        start_datetime=start_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        end_datetime=end_datetime.strftime(DatetimeUtils.ISO8601_FORMAT)
    )
    event_data.update(data)
    response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
    logger.info(response.text)
    assert response.status_code == codes.CREATED, response.text
