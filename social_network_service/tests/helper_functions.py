"""
Helper methods used in social network service test cases. like to create event test data for event creation
or send request
"""
# Std Imports
import json
import datetime

# Third Party
import requests
from requests import codes

# Service imports
from social_network_service.common.models.db import db
from social_network_service.common.models.event import Event
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.utils.graphql_utils import validate_graphql_response, get_query
from social_network_service.social_network_app import logger
from social_network_service.common.utils.handy_functions import send_request
from social_network_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from social_network_service.common.campaign_services.tests.modules.helper_functions import auth_header


def get_headers(token):
    """
    Return header dictionary containing bearer token and content-type
    :param token: bearer token
    :return: dictionary containing bearer token
    """
    return {'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'}


def unauthorize_test(method, url, data=None):
    response = send_request(method, url, 'invalid_token', data)
    assert response.status_code == 401, 'It should be unauthorized (401)'
    return response


def event_data_tests(method, url, data, token):
    """

    :param method:
    :param url:
    :param data:
    :param token:
    :return:
    """
    event = data.copy()

    # Update with invalid event id
    event['id'] = 231232132133  # We will find a better way to test it
    response = send_request(method, url, token, data=event)
    # response = send_post_request(SocialNetworkApiUrl.EVENT % event['id'],
    #                              event, token)
    logger.info(response.text)
    assert response.status_code == 404, 'Event not found with this id'

    # Update with invalid social network event id
    event = data.copy()
    event['social_network_event_id'] = -1
    response = send_request(method, url, token, data=event)
    logger.info(response.text)
    assert response.status_code == 404, 'Event not found with this social network event id'

    event = data.copy()

    # success case, event should be updated
    datetime_now = datetime.datetime.now()
    event['title'] = 'Test update event'
    event['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
    event['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')
    response = send_request(method, url, token, data=event)
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


def assert_event(user_id, social_network_event_id):
    """
    This asserts we get event in database for given user_id and social_network_event_id
    """
    db.session.commit()
    event = Event.get_by_user_and_social_network_event_id(user_id=user_id,
                                                          social_network_event_id=social_network_event_id)
    assert event


def get_graphql_data(query, token, expected_status=(codes.OK,)):
    """
    This function is to avoid some redundant, repeatable code like passing SN service url, asserting OK response etc.
    :param dict query: GraphQL query for SN service endpoint
    :param string token: access token
    :param list | tuple expected_status: list/tuple of HTTP status codes
    """
    print('Query: %s' % query)
    response = send_request('get', SocialNetworkApiUrl.GRAPHQL, token, data=query)
    print('get_graphql_data. Response: %s' % response.content)
    assert response.status_code in expected_status
    json_response = response.json()
    return json_response


def assert_valid_response(key, model, token, obj_id, ignore_id_test=False):
    """
    This helper function gets data from SN service Graphql endpoint according to given model and id of the object
    and validates expected fields in response.
    :param string key: root response object key
    :param db.Model model: model class
    :param string token: access token
    :param int obj_id: object id
    :param bool ignore_id_test: True if you want to skip single object test
    """
    fields = model.get_fields()
    query = get_query(key + 's', fields)
    response = get_graphql_data(query, token)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response(key + 's', response['data'], fields, is_array=True)
    if not ignore_id_test:
        query = get_query(key, fields, args=dict(id=obj_id))
        response = get_graphql_data(query, token)
        assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
        validate_graphql_response(key, response['data'], fields)
    return response


def match_data(graphql_obj, restful_obj, fields):
    """
    This helper method takes graphql response object and object returned from restful api and matches given fields.
    :param dict graphql_obj: graphql response object
    :param dict restful_obj: object returned from restful api or by using `to_json()` method on model instance
    :param list | tuple fields: list of fields to be matched
    """
    for field in fields:
        graphql_obj[field] = '' if graphql_obj[field] is None else graphql_obj[field]
        assert graphql_obj[field] == restful_obj[field], 'field: %s, GraphqlObj: %s\nRestfulObj: %s' \
                                                         % (field, graphql_obj, restful_obj)


def match_event_fields(event):
    """
    This helper method checks if expected fields of event exist or not
    :param event: event response object
    """
    assert event['added_datetime']
    CampaignsTestsHelpers.assert_valid_datetime_range(str(event['added_datetime']), minutes=5)
    assert event['updated_datetime']
    CampaignsTestsHelpers.assert_valid_datetime_range(str(event['updated_datetime']), minutes=5)
    assert event['social_network_event_id']
    assert event['social_network_id']
    assert event['id']


def match_venue_fields(venue):
    """
    This helper method checks if expected fields of venue exist or not
    :param venue: venue response object
    """
    assert venue['added_datetime']
    CampaignsTestsHelpers.assert_valid_datetime_range(str(venue['added_datetime']), minutes=5)
    assert venue['updated_datetime']
    CampaignsTestsHelpers.assert_valid_datetime_range(str(venue['updated_datetime']), minutes=5)
    assert venue['id']
    assert venue['social_network_venue_id']
    assert venue['social_network_id']


def match_event_organizer_fields(event_organizer):
    """
    This helper method checks if expected fields of event organizer exist or not
    :param event_organizer: event organizer response object
    """
    assert event_organizer['added_datetime']
    CampaignsTestsHelpers.assert_valid_datetime_range(str(event_organizer['added_datetime']), minutes=5)
    assert event_organizer['updated_datetime']
    CampaignsTestsHelpers.assert_valid_datetime_range(str(event_organizer['updated_datetime']), minutes=5)
    assert event_organizer['id']
