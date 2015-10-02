import json
import datetime
import requests
from gt_common.models.organizer import Organizer
from gt_common.models.venue import Venue
from social_network_service.manager import delete_events
from social_network_service.utilities import convert_keys_to_camel_case
from gt_common.models.event import Event

API_URL = 'http://127.0.0.1:5000'
GET_TOKEN = 'http://127.0.0.1:8888/oauth2/token'


class TestResourceEvents:

    def test_get_with_invalid_token(self):
        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_get_with_valid_token(self, auth_data):

        response = requests.get(API_URL + '/events/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        events = response.json()['events']
        assert len(events) > 0, 'There should be some events for test user'

    def test_post_with_invalid_token(self):
        response = requests.post(API_URL + '/events/', data=dict(a='a', b='b'),  headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'events' not in response.json()

    def test_post_with_valid_token(self,user, auth_data, test_event):
        event_data = test_event
        response = requests.post(API_URL + '/events/', data=json.dumps(event_data),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 201, 'Status should be Ok, Resource Created (201)'
        event_id = response.json()['id']
        assert event_id > 0, 'Event id should be a positive number'
        test_event['id'] = event_id     # Add created event id  in test_event so it can be deleted in tear_down

    def test_eventbrite_with_missing_required_fields(self, auth_data, eventbrite_missing_data):
        key, event_data = eventbrite_missing_data
        event_data[key] = ''
        response = requests.post(API_URL + '/events/', data=json.dumps(event_data),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 453, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_missing_required_fields(self, auth_data, meetup_missing_data):
        key, event_data = meetup_missing_data
        event_data[key] = ''
        response = requests.post(API_URL + '/events/', data=json.dumps(event_data),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 453, 'There should be an missing field error for %s KeyError' % key

    def test_meetup_with_valid_address(self, user, auth_data, meetup_event_data):
        event_data = meetup_event_data
        response = requests.post(API_URL + '/events/', data=json.dumps(event_data),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 201, 'Event should be created, address is valid'
        event_id = response.json()['id']
        meetup_event_data['id'] = event_id

    def test_meetup_with_invalid_address(self, auth_data, meetup_event_data):
        event_data = meetup_event_data
        event_data['venue_id'] = 2
        response = requests.post(API_URL + '/events/', data=json.dumps(event_data),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 458, 'Event should not be created, address is invalid according to Meetup API'


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
        datetime_now = datetime.datetime.now()
        event['title'] = 'Test update event'
        event['start_datetime'] = (datetime_now + datetime.timedelta(days=50)).strftime('%Y-%m-%d %H:%M:%S')
        event['end_datetime'] = (datetime_now + datetime.timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')
        response = requests.post(API_URL + '/events/' + str(event['id']), data=json.dumps(event),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 204, 'Status should be Ok, Resource Modified (204)'
        event_db = Event.get_by_id(event['id'])
        Event.session.commit()  # needed to refresh session otherwise it will show old objects
        event_db = event_db.to_json()
        assert event['title'] == event_db['title'], 'event_title is modified'
        assert event['start_datetime'] == event_db['start_datetime'], 'event_start_datetime is modified'
        assert event['end_datetime'] == event_db['end_datetime'], 'event_end_datetime is modified'

    def test_delete_with_invalid_token(self, event_in_db):
        response = requests.delete(API_URL + '/events/' + str(event_in_db.id), headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, auth_data, event_in_db):
        response = requests.delete(API_URL + '/events/' + str(event_in_db.id), headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'


class TestVenues:

    def test_get_with_invalid_token(self):
        response = requests.post(API_URL + '/venues/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'venues' not in response.json()

    def test_get_with_valid_token(self, auth_data):
        response = requests.get(API_URL + '/venues/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'venues' in results

    def test_post_with_invalid_token(self):
        response = requests.post(API_URL + '/venues/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, auth_data):
        venue = {
            "social_network_id": 18,
            "zipcode": "54600",
            "address_line2": "H# 163, Block A",
            "address_line1": "New Muslim Town",
            "latitude": 0,
            "longitude": 0,
            "state": "CA",
            "city": "Lahore",
            "country": "Pakistan"
        }
        response = requests.post(API_URL + '/venues/', data=json.dumps(venue),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 201, 'Status should be Ok, Resource created (201)'
        response = response.json()
        assert response['id'] > 0
        Venue.session.commit()
        venue = Venue.get_by_id(response['id'])
        assert venue, 'Venue created successfully in db'
        Venue.delete(venue.id)

    def test_delete_with_invalid_token(self):

        response = requests.delete(API_URL + '/venues/', data=json.dumps({'ids': []}),
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, auth_data, venue_in_db):
        venue_ids = {'ids': [venue_in_db.id]}
        response = requests.delete(API_URL + '/venues/',  data=json.dumps(venue_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'


class TestOrganizers:

    def test_get_with_invalid_token(self):
        response = requests.post(API_URL + '/organizers/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'organizers' not in response.json()

    def test_get_with_valid_token(self, auth_data):
        response = requests.get(API_URL + '/organizers/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'organizers' in results

    def test_post_with_invalid_token(self, user):
        organizer = {
            "user_id": user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/organizers/', data=json.dumps(organizer),
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, auth_data, user):
        organizer = {
            "user_id": user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/organizers/', data=json.dumps(organizer),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 201, 'Status should be Ok, Resource created (201)'
        response = response.json()
        assert response['id'] > 0
        Organizer.session.commit()
        organizer = Organizer.get_by_id(response['id'])
        assert organizer, 'Organizer created successfully in db'
        Organizer.delete(organizer.id)

    def test_delete_with_invalid_token(self):

        response = requests.delete(API_URL + '/organizers/', data=json.dumps({'ids': []}),
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, auth_data, organizer_in_db):
        organizer_ids = {'ids': [organizer_in_db.id]}
        response = requests.delete(API_URL + '/organizers/',  data=json.dumps(organizer_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'

