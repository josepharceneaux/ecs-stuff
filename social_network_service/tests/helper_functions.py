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
from social_network_service.social_network_app import logger
from social_network_service.common.utils.handy_functions import send_request


def auth_header(token):
    """
    Return dictionary which consist of bearer token only.
    :param token: bearer token
    :return:dictionary containing bearer token
    """
    return dict(Authorization='Bearer %s' % token)


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
    :return:
    """
    print('Query: %s' % query)
    response = send_request('get', SocialNetworkApiUrl.GRAPHQL, token, data=query)
    print('get_graphql_data. Response: %s' % response.content)
    assert response.status_code in expected_status
    json_response = response.json()
    return json_response
