import json
import requests
from social_network_service import flask_app as app
from common.models.organizer import Organizer

API_URL = app.config['APP_URL']


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

    def test_post_with_invalid_token(self, test_user):
        organizer = {
            "user_id": test_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/organizers/', data=json.dumps(organizer),
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, auth_data, test_user):
        organizer = {
            "user_id": test_user.id,
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
