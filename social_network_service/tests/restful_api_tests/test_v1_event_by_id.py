# Std imports
import datetime
import json

import requests
import sys

# Application imports
from social_network_service.common.activity_service_config import ActivityServiceKeys
from social_network_service.common.models.event import Event
from social_network_service.common.models.misc import Activity
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.social_network_app import logger
from social_network_service.tests.helper_functions import auth_header, get_headers, send_request, \
    event_data_tests, unauthorize_test


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

    def test_putw_invalid_event_id(self, token, event_in_db):
        """
        - Get event data from db (using fixture - event_in_db)
        :param token:
        :param event_in_db:
        :return:
        """
        event = event_in_db.to_json()

        # Update with invalid event id
        event['id'] = sys.maxint  # We will find a better way to test it
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token, data=event)

        logger.info(response.text)
        assert response.status_code == 404, 'Event not found with this id'

    def test_putw_invalid_event_id_(self, token, event_in_db):
        """
        - Get event data from db (using fixture - event_in_db)
        - Modify social_network_id to -1 in event data object
        - Send request to update event data. response should be 404 as there is no social network id = -1
        :param token:
        :param event_in_db:
        :return:
        """
        event = event_in_db.to_json()
        event_id = event['id']

        # Update with invalid event id
        event['id'] = sys.maxint  # We will find a better way to test it

        # Update with invalid social network event id
        event['id'] = event_id
        event['social_network_event_id'] = -1
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token, data=event)
        logger.info(response.text)
        assert response.status_code == 404, 'Event not found with this social network event id'

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
        social_network_event_id = event['social_network_event_id']

        event['social_network_event_id'] = social_network_event_id

        # Success case, event should be updated
        datetime_now = datetime.datetime.now()
        event['title'] = 'Test update event'
        event['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
        event['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token, data=event)
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok, Resource Modified (200)'
        event_db = Event.get_by_id(event['id'])
        Event.session.commit()  # needed to refresh session otherwise it will show old objects
        event_db = event_db.to_json()
        assert event['title'] == event_db['title'], 'event_title is modified'
        assert event['start_datetime'] == event_db['start_datetime'].replace(' ', 'T') + 'Z', \
            'start_datetime is modified'
        assert event['end_datetime'] == event_db['end_datetime'].replace(' ', 'T') + 'Z', \
            'end_datetime is modified'

        # Check activity updated
        activity = Activity.get_by_user_id_type_source_id(source_id=event['id'],
                                                          type=ActivityServiceKeys.EVENT_UPDATE,
                                                          user_id=event_db['user_id'])

        data = json.loads(activity.params)
        assert data['eventTitle'] == event['title']

    def test_delete_with_invalid_token(self, event_in_db):
        """
        - Try to delete event data using id and pass invalid access token in header
        - it should throw 401 un-authorized exception
        :param event_in_db:
        :return:
        """
        unauthorize_test('delete', url=SocialNetworkApiUrl.EVENT % event_in_db.id)

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

    def test_activity_created(self, token, event_in_db):
        event = event_in_db.to_json()
        activities = Activity.get_by_user_id_type_source_id(user_id=event['user_id'],
                                                            source_id=event['id'],
                                                            type=ActivityServiceKeys.EVENT_CREATE)
        data = json.loads(activities.params)
        assert data['eventTitle'] == event['title']
