"""
Helper methods used in social network service test cases. like to create event test data for event creation
or send request
"""

# Std Imports
import json
import datetime
import requests

# Service imports
from social_network_service.common.models.event import Event
from social_network_service.social_network_app import logger


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
    response = send_request(method, url, 'invalid_token',  data)
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


def send_request(method, url, access_token, data=None, is_json=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


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