import json
import requests
from social_network_service import flask_app as app
from common.models.event_organizer import EventOrganizer

API_URL = app.config['APP_URL']


class TestOrganizers:

    def test_get_with_invalid_token(self):
        response = requests.post(API_URL + '/event_organizers/', headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'organizers' not in response.json()

    def test_get_with_valid_token(self, auth_data):
        response = requests.get(API_URL + '/event_organizers/', headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'event_organizers' in results

    def test_post_with_invalid_token(self, test_user):
        event_organizer = {
            "user_id": test_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/event_organizers/', data=json.dumps(event_organizer),
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, auth_data, test_user):
        event_organizer = {
            "user_id": test_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/event_organizers/', data=json.dumps(event_organizer),
                                 headers={'Authorization': 'Bearer %s' % auth_data['access_token'],
                                          'Content-Type': 'application/json'})
        assert response.status_code == 201, 'Status should be Ok, Resource created (201)'
        assert 'Location' in response.headers
        response = response.json()
        assert response['id'] > 0
        EventOrganizer.session.commit()
        event_organizer = EventOrganizer.get_by_id(response['id'])
        assert event_organizer, 'Event organizer created successfully in db'
        EventOrganizer.delete(event_organizer.id)

    def test_delete_with_invalid_token(self):

        response = requests.delete(API_URL + '/event_organizers/', data=json.dumps({'ids': []}),
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, auth_data, organizer_in_db):
        organizer_ids = {'ids': [organizer_in_db.id]}
        response = requests.delete(API_URL + '/event_organizers/',  data=json.dumps(organizer_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 200, 'Status should be Ok (200)'

        organizer_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(API_URL + '/event_organizers/',  data=json.dumps(organizer_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 207, 'Unable to delete all organizers (207)'
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

        organizer_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(API_URL + '/event_organizers/',  data=json.dumps(organizer_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 400, 'Bad Request'
        response = response.json()
        assert response['error']['code'] == 400, 'Bad Request'
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'
