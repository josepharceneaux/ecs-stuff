"""
This file contain tests for events api
"""

# Std imports
import json
import datetime
import sys

# Third-Part imports
import requests

# App specific imports
from social_network_service.common.models.event import Event
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.tests.helper_functions import auth_header, get_headers, send_request, \
    event_data_tests, unauthorize_test


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
        - As the test user is newly created, so there will be no events
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

        response = requests.get(SocialNetworkApiUrl.EVENTS, headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) > 0, 'There should be some events for test user'

    def test_events_post_with_invalid_token(self):
        response = send_post_request(SocialNetworkApiUrl.EVENTS, {}, 'invalid_token')
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_events_post_with_valid_token(self, token, test_event):
        event_data = test_event
        social_network_id = event_data['social_network_id']
        venue_id = event_data['venue_id']
        organizer_id = event_data['organizer_id']

        # test with a social network that does not exists
        event_data['social_network_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4052, 'Social Network not found'

        # test social network which have no implementation for events
        event_data['social_network_id'] = 1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4062, 'Social Network have no events implementation'

        event_data['social_network_id'] = social_network_id

        # test with invalid organizer
        event_data['organizer_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4054, 'Event organizer not found'

        event_data['organizer_id'] = organizer_id

        # test with invalid venue
        event_data['venue_id'] = -1
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4065, 'Venue not found'

        event_data['venue_id'] = venue_id

        # Now test with invalid start datetime UTC format
        datetime_now = datetime.datetime.now()
        event_data['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%S')
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4064, 'Invalid start datetime format'

        # Now test with invalid end datetime UTC format
        event_data['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
        event_data['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S')
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4064, 'Invalid end datetime format'
        event_data['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Success case
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 201, 'Status should be Ok, Resource Created (201)'
        assert 'Location' in response.headers
        event_id = response.json()['id']
        assert event_id > 0, 'Event id should be a positive number'
        test_event['id'] = event_id     # Add created event id  in test_event so it can be deleted in tear_down

    def test_eventbrite_with_missing_required_fields(self, token, eventbrite_missing_data,
                                                     test_eventbrite_credentials):
        key, event_data = eventbrite_missing_data
        event_data[key] = ''
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500, 'It should fail'
        response = response.json()
        assert response['error']['code'] == 4053, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_missing_required_fields(self, token, meetup_missing_data, test_meetup_credentials):
        key, event_data = meetup_missing_data
        event_data[key] = ''
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500, 'It should fail'
        response = response.json()
        assert response['error']['code'] == 4053, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_valid_address(self, token, meetup_event_data, test_meetup_credentials):
        event_data = meetup_event_data
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 201, 'Event should be created, address is valid'
        event_id = response.json()['id']
        meetup_event_data['id'] = event_id

    def test_meetup_with_invalid_address(self, token, meetup_event_data, test_meetup_credentials):
        event_data = meetup_event_data
        event_data['venue_id'] = 2
        response = send_post_request(SocialNetworkApiUrl.EVENTS, event_data, token)
        logger.info(response.text)
        assert response.status_code == 500, 'Internal Server Error'
        response = response.json()
        assert response['error']['code'] == 4065, \
            'Event should not be created, address is invalid according to Meetup API'


class TestEventById:
    """
    Test event using event id like
    - try to get event using id and pass invalid access token in auth header        - 401 response
    - try to get event using id and pass access token in auth header                - 200 response
    - try to put event data using id and pass invalid access token in auth header   - 401 response
    - try to put event data using id and pass valid access token in auth header     - 200 response
    - try deleting event data using id and pass invalid access token                - 401 response
    - try deleting event data using id and pass valid token                         - 200 response
    """
    def test_get_by_id_with_invalid_token(self):
        """
        - Get event using id and pass invalid token and it should throw exception 401 un-authorize
        - Also make sure if event is present in response data
        :return:
        """
        response = unauthorize_test(url=SocialNetworkApiUrl.EVENT % 1,
                                    method='get'
                                    )
        assert 'event' not in response.json()

    def test_get_by_id_with_valid_token(self, token, event_in_db):
        """
        - Get event using id and response should be 200
        - Delete venue_id and organizer_id from event response data
        - Then compare values from the event data in db table and response event data
        :param token:
        :param event_in_db:
        :return:
        """
        event = event_in_db

        response = requests.get(SocialNetworkApiUrl.EVENT % event.id,
                                headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'event' in results
        api_event = results['event']
        event = event.to_json()
        del event['venue_id']
        del event['organizer_id']
        comparison = '\n{0: <20}  |  {1: <40} |  {2: <40}\n'.format('Key', 'Expected', 'Found')
        comparison += '=' * 100 + '\n'
        status = True
        for key, val in event.items():
            mismatch = ''
            if event[key] == api_event[key]:
                mismatch = '**'
            comparison += '{0: <20}  {1}|  {2: <40} |  {3: <40}\n'.format(key, mismatch, event[key], api_event[key])
            comparison += '-' * 100 + '\n'
            status = status and event[key] == api_event[key]

        assert status, 'Event values were not matched\n' + comparison

    def test_put_with_invalid_token(self):
        """
        - Try to send data using invalid access_token in header and it should give 401 (unauthorized error)
        :return:
        """
        unauthorize_test('put', url=SocialNetworkApiUrl.EVENT % 1,
                         data={})

    def test_put_with_valid_token(self, token, event_in_db):
        """
        - Get event data from db (using fixture - event_in_db)
        - Modify event id to highest possible int number
        - Using event id, send PUT request to update event data
        - Should get 404 response because event doesn't exist
        :param token:
        :param event_in_db:
        :return:
        """
        event = event_in_db.to_json()
        event_id = event['id']
        social_network_event_id = event['social_network_event_id']

        # Update with invalid event id
        event['id'] = sys.maxint  # We will find a better way to test it
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token, data=event)

        logger.info(response.text)
        assert response.status_code == 404, 'Event not found with this id'

        # Update with invalid social network event id
        event['id'] = event_id
        event['social_network_event_id'] = -1
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token, data=event)
        logger.info(response.text)
        assert response.status_code == 404, 'Event not found with this social network event id'

        event['social_network_event_id'] = social_network_event_id

        # Success case, event should be updated
        datetime_now = datetime.datetime.now()
        event['title'] = 'Test update event'
        event['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
        event['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token, data=event)
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok, Resource Modified (204)'
        event_db = Event.get_by_id(event['id'])
        Event.session.commit()  # needed to refresh session otherwise it will show old objects
        event_db = event_db.to_json()
        assert event['title'] == event_db['title'], 'event_title is modified'
        assert event['start_datetime'] == event_db['start_datetime'].replace(' ', 'T') + 'Z', \
            'start_datetime is modified'
        assert event['end_datetime'] == event_db['end_datetime'].replace(' ', 'T') + 'Z', \
            'end_datetime is modified'

    def test_delete_with_invalid_token(self, event_in_db):
        """
        - Try to delete event data using id and pass invalid access token in header
        - it should throw 401 un-authorized exception
        :param event_in_db:
        :return:
        """
        unauthorize_test('DELETE', url=SocialNetworkApiUrl.EVENT % event_in_db.id)

    def test_delete_with_valid_token(self, token, event_in_db):
        """
        - Try to delete event data using id, if deleted you expect 200 response
        - Then again try to delete event using same event id and expect 403 response
        """
        event_id = event_in_db.id
        response = requests.delete(SocialNetworkApiUrl.EVENT % event_id,
                                   headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        response = requests.delete(SocialNetworkApiUrl.EVENT % event_id,
                                   headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 403, 'Unable to delete event as it is not present there (403)'


"""
SECTION: Helper methods for tests
"""


def send_post_request(url, data, access_token):
    """
    This method sends a post request to a URL with given data using access_token for authorization in header
    :param url: URL where post data needs to be sent
    :param data: Data which needs to be sent
    :param access_token: User access_token for authorization
    :return:
    """
    return requests.post(url, data=json.dumps(data),
                         headers=get_headers(access_token))


