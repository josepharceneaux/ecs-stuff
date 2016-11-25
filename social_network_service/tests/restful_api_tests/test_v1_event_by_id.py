"""
Test cases for meetup and eventbrite event i.e get/delete event by id or using with valid and invalid token.
"""
# Std imports
import copy
import json
import sys
import datetime

# Third Party
import requests
from requests import codes

# Application imports
from social_network_service.common.models import db
from social_network_service.social_network_app import logger
from social_network_service.common.models.event import Event
from social_network_service.common.models.misc import Activity
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.utils.handy_functions import send_request
from social_network_service.common.utils.datetime_utils import DatetimeUtils
from social_network_service.tests.helper_functions import auth_header, unauthorize_test
from social_network_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestEventById(object):
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
        """
        non_existing_id = CampaignsTestsHelpers.get_non_existing_id(Event)
        response = unauthorize_test(url=SocialNetworkApiUrl.EVENT % non_existing_id, method='get')
        assert 'event' not in response.json()

    def test_get_by_id_with_valid_token(self, token_first, token_same_domain, event_in_db_second):
        """
        - Get event using id and response should be 200
        - Get event by some other user of same domain using id and response should be 200
        - Delete venue_id and organizer_id from event response data
        - Then compare values from the event data in db table and response event data
        """
        event = copy.deepcopy(event_in_db_second)
        for access_token in (token_first, token_same_domain):
            response = requests.get(SocialNetworkApiUrl.EVENT % event['id'], headers=auth_header(access_token))
            logger.info(response.text)
            assert response.status_code == codes.OK, "Response: {}".format(response.text)
            results = response.json()
            assert 'event' in results
            api_event = results['event']
            if event.get('venue_id'):
                del event['venue_id']
            if event.get('organizer_id'):
                del event['organizer_id']
            comparison = '\n{0: <20}  |  {1: <40} |  {2: <40}\n'.format('Key', 'Expected', 'Found')
            comparison += '=' * 100 + '\n'
            status = True
            for key, val in event.items():
                mismatch = ''
                if event[key] == api_event[key]:
                    mismatch = '**'
                comparison += '{0: <20}  {1}|  {2: <40} |  {3: <40}\n'.format(key, mismatch, event[key],
                                                                              api_event[key])
                comparison += '-' * 100 + '\n'
                status = status and event[key] == api_event[key]

            assert status, 'Event values were not matched\n' + comparison

    def test_put_with_invalid_token(self):
        """
        - Try to send data using invalid access_token in header and it should give 401 (unauthorized error)
        """
        non_existing_id = CampaignsTestsHelpers.get_non_existing_id(Event)
        unauthorize_test('put', url=SocialNetworkApiUrl.EVENT % non_existing_id, data={})

    def test_put_with_invalid_event_id(self, token_first, event_in_db):
        """
        - Get event data from db (using fixture - event_in_db)
        """
        event = copy.deepcopy(event_in_db)

        # Update with invalid event id
        event['id'] = sys.maxint  # We will find a better way to test it
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token_first, data=event)

        logger.info(response.text)
        assert response.status_code == codes.NOT_FOUND, 'Event not found with this id'

    def test_put_with_invalid_event_id_and_sn(self, token_first, event_in_db):
        """
        - Get event data from db (using fixture - event_in_db)
        - Modify social_network_id to max int value in event data object
        - Send request to update event data. response should be 404 as there is no social network id = max int
        """
        event = copy.deepcopy(event_in_db)
        event_id = event['id']

        # Update with invalid event id
        event['id'] = sys.maxint  # We will find a better way to test it

        # Update with invalid social network event id
        event['id'] = event_id
        event['social_network_event_id'] = sys.maxint
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token_first, data=event)
        logger.info(response.text)
        assert response.status_code == codes.NOT_FOUND, 'Event not found with this social network event id'

    def test_put_with_valid_token(self, token_first, event_in_db_second):
        """
        - Get event data from db (using fixture - event_in_db)
        - Using event id, send PUT request to update event data
        - Should get 200 response
        - Check if activity is created or not
        """
        event = copy.deepcopy(event_in_db_second)
        # Success case, event should be updated
        datetime_now = datetime.datetime.utcnow()
        datetime_now = datetime_now.replace(microsecond=0)
        event['title'] = 'Test update event'
        event['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime(DatetimeUtils.ISO8601_FORMAT)
        event['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime(DatetimeUtils.ISO8601_FORMAT)
        response = send_request('put', SocialNetworkApiUrl.EVENT % event['id'], token_first, data=event)
        logger.info(response.text)
        assert response.status_code == codes.OK, '{} {}'.format(response.text, event)
        db.db.session.commit()
        event_occurrence_in_db = Event.get_by_id(event['id'])
        Event.session.commit()  # needed to refresh session otherwise it will show old objects
        event_occurrence_in_db = event_occurrence_in_db.to_json()
        assert event['title'] == event_occurrence_in_db['title'], 'event_title is modified'
        assert event['start_datetime'].split('.')[0] + 'Z' == event_occurrence_in_db['start_datetime'] \
                                                                  .replace(' ', 'T') + 'Z', \
            'start_datetime is modified'
        assert (event['end_datetime']).split('.')[0] + 'Z' == event_occurrence_in_db['end_datetime'] \
                                                                  .replace(' ', 'T') + 'Z', \
            'end_datetime is modified'

        # Check activity updated
        activity = Activity.get_by_user_id_type_source_id(source_id=event['id'],
                                                          type_=Activity.MessageIds.EVENT_UPDATE,
                                                          user_id=event_occurrence_in_db['user_id'])

        data = json.loads(activity.params)
        assert data['event_title'] == event['title']

    def test_delete_with_invalid_token(self, event_in_db):
        """
        - Try to delete event data using id and pass invalid access token in header
        - it should throw 401 un-authorized exception
        """
        unauthorize_test('delete', url=SocialNetworkApiUrl.EVENT % event_in_db['id'])

    def test_delete_with_valid_token(self, token_first, event_in_db):
        """
        - Try to delete event data using id, if deleted you expect 200 response
        - Then again try to delete event using same event id and expect 403 response
        """
        event_id = event_in_db['id']
        response = requests.delete(SocialNetworkApiUrl.EVENT % event_id, headers=auth_header(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, str(response.text)
        response = requests.delete(SocialNetworkApiUrl.EVENT % event_id, headers=auth_header(token_first))

        # check if event delete activity
        user_id = event_in_db['user_id']
        db.db.session.commit()
        activity = Activity.get_by_user_id_type_source_id(user_id=user_id, source_id=event_id,
                                                          type_=Activity.MessageIds.EVENT_DELETE)
        data = json.loads(activity.params)
        assert data['event_title'] == event_in_db['title']

        logger.info(response.text)
        assert response.status_code == codes.FORBIDDEN, 'Unable to delete event as it is not present there (403)'
