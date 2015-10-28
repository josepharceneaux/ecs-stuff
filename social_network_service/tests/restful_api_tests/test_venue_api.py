import json
import requests
from social_network_service import flask_app as app
from common.models.venue import Venue

API_URL = app.config['APP_URL']


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
        assert 'Location' in response.headers
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

        venue_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(API_URL + '/venues/',  data=json.dumps(venue_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 207, 'Unable to delete all venues (207)'
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

        venue_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(API_URL + '/venues/',  data=json.dumps(venue_ids),
                                   headers=dict(Authorization='Bearer %s' % auth_data['access_token']))
        assert response.status_code == 400, 'Bad Request'
        response = response.json()
        assert response['error']['code'] == 400, 'Bad Request'
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'

