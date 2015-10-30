import json
import datetime
import requests
from social_network_service import flask_app as app
from social_network_service.common.models.event import Event

API_URL = app.config['APP_URL']

# TODO comment all tests , on the top and each method


class TestResourceEvents:

    def test_get_with_invalid_token(self):
        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_events_get_with_valid_token(self, auth_data):

        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) == 0, 'There should be some events for test user'

    def test_events_get_with_valid_token(self, auth_data, event_in_db):

        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) > 0, 'There should be some events for test user'

    def test_events_post_with_invalid_token(self):
        response = send_post_request('/events/', {}, 'invalid_token')
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_events_post_with_valid_token(self, auth_data, test_event):
        event_data = test_event
        social_network_id = event_data['social_network_id']
        venue_id = event_data['venue_id']
        organizer_id = event_data['organizer_id']

        # test with a social network that does not exists
        event_data['social_network_id'] = -1
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4052, 'Social Network not found'

        # test social network which have no implementation for events
        event_data['social_network_id'] = 1
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4062, 'Social Network have no events implementation'

        event_data['social_network_id'] = social_network_id

        # test with invalid organizer
        event_data['organizer_id'] = -1
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4054, 'Event organizer not found'

        event_data['organizer_id'] = organizer_id

        # test with invalid venue
        event_data['venue_id'] = -1
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4065, 'Venue not found'

        event_data['venue_id'] = venue_id

        # Now test with invalid start datetime UTC format
        datetime_now = datetime.datetime.now()
        event_data['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%S')
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4064, 'Invalid start datetime format'

        # Now test with invalid end datetime UTC format
        event_data['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
        event_data['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S')
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500
        response = response.json()
        assert 'error' in response and response['error']['code'] == 4064, 'Invalid end datetime format'
        event_data['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Success case
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 201, 'Status should be Ok, Resource Created (201)'
        assert 'Location' in response.headers
        event_id = response.json()['id']
        assert event_id > 0, 'Event id should be a positive number'
        test_event['id'] = event_id     # Add created event id  in test_event so it can be deleted in tear_down

    def test_eventbrite_with_missing_required_fields(self, auth_data, eventbrite_missing_data):
        key, event_data = eventbrite_missing_data
        event_data[key] = ''
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500, 'It should fail'
        response = response.json()
        assert response['error']['code'] == 4053, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_missing_required_fields(self, auth_data, meetup_missing_data):
        key, event_data = meetup_missing_data
        event_data[key] = ''
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500, 'It should fail'
        response = response.json()
        assert response['error']['code'] == 4053, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_valid_address(self, auth_data, meetup_event_data):
        event_data = meetup_event_data
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 201, 'Event should be created, address is valid'
        event_id = response.json()['id']
        meetup_event_data['id'] = event_id

    def test_meetup_with_valid_address(self, auth_data, meetup_event_data):
        event_data = meetup_event_data
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 201, 'Event should be created, address is valid'
        event_id = response.json()['id']
        meetup_event_data['id'] = event_id

    def test_meetup_with_invalid_address(self, auth_data, meetup_event_data):
        event_data = meetup_event_data
        event_data['venue_id'] = 2
        response = send_post_request('/events/', event_data, auth_data['access_token'])
        assert response.status_code == 500, 'Internal Server Error'
        response = response.json()
        assert response['error']['code'] == 4065, \
            'Event should not be created, address is invalid according to Meetup API'


class TestEventById:

    def test_get_with_invalid_token(self):
        response = requests.post(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'event' not in response.json()

    def test_get_with_valid_token(self, auth_data, event_in_db):
        event = event_in_db

        response = requests.get(API_URL + '/events/' + str(event.id), headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
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

        assert status == True, 'Event values were not matched\n' + comparison

    def test_post_with_invalid_token(self):
        response = requests.post(API_URL + '/events/1', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, auth_data, event_in_db):

        event = event_in_db.to_json()
        event_id = event['id']
        social_network_event_id = event['social_network_event_id']

        # Update with invalid event id
        event['id'] = 231232132133  # We will find a better way to test it
        response = send_post_request('/events/' + str(event['id']),
                                     event, auth_data['access_token'])
        assert response.status_code == 404, 'Event not found with this id'
        response = response.json()
        assert response['error']['code'] == 404, 'Error code should be 404'

        # Update with invalid social network event id
        event['id'] = event_id
        event['social_network_event_id'] = -1
        response = send_post_request('/events/' + str(event['id']),
                                     event, auth_data['access_token'])
        assert response.status_code == 404, 'Event not found with this social network event id'
        response = response.json()
        assert response['error']['code'] == 404, 'Error code should be 404'

        event['social_network_event_id'] = social_network_event_id

        # success case, event should be updated
        datetime_now = datetime.datetime.now()
        event['title'] = 'Test update event'
        event['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%dT%H:%M:%SZ')
        event['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%SZ')
        response = send_post_request('/events/' + str(event['id']),
                                     event, auth_data['access_token'])
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
        response = requests.delete(API_URL + '/events/' + str(event_in_db.id), headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, auth_data, event_in_db):
        event_id = event_in_db.id
        response = requests.delete(API_URL + '/events/' + str(event_id), headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        response = requests.delete(API_URL + '/events/' + str(event_id), headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 403, 'Unable to delete event as it is not present there (403)'


def send_post_request(relative_url, data, access_token):
    return requests.post(API_URL + relative_url, data=json.dumps(data),
                         headers={'Authorization': 'Bearer %s' % access_token,
                                  'Content-Type': 'application/json'})