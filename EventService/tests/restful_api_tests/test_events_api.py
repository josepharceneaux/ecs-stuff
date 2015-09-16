import json
import pytest
import requests

API_URL = 'http://127.0.0.1:5000'
GET_TOKEN = 'http://127.0.0.1:8888/oauth2/token'


data = dict(eventTitle='Test Event',
            eventDescription='Test Event Description',
            socialNetworkId=12)
meetup_event = data.copy()
eventbrite_event = data.copy()
eventbrite_event['socialNetworkId'] = 18


class TestResourceEvents:

    def test_get_with_invalid_token(self):
        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_get_with_valid_token(self, auth_data):
        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) == 0, 'There should be no events for test user'

    def test_post_with_invalid_token(self):
        response = requests.post(API_URL + '/events/', data=dict(a='a', b='b'),  headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    @pytest.mark.parametrize("data", [meetup_event, eventbrite_event])
    def test_post_with_valid_token(self, auth_data, data):
        response = requests.post(API_URL + '/events/', data=json.dumps(data),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 201, 'Status should be Ok, Resource Created (201)'
        event_id = response.json()['id']
        assert event_id > 0, 'Event id should be a positive number'


class TestEventById:

    def test_get_with_invalid_token(self):
        response = requests.post(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'event' not in response.json()

    def test_get_with_valid_token(self, auth_data):
        response = requests.get(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'event' in results
        event = results['event']

    def test_post_with_invalid_token(self):
        response = requests.post(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, auth_data):
        response = requests.post(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 204, 'Status should be Ok, Resource Modified (204)'

    def test_delete_with_invalid_token(self):
        response = requests.delete(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, auth_data):
        response = requests.delete(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
