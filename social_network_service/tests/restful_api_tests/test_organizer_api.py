import json
import requests

from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.tests.helper_functions import auth_header, get_headers

API_URL = SocialNetworkApiUrl.HOST_NAME % '/v1'


class TestOrganizers:

    def test_get_with_invalid_token(self):
        response = requests.post(API_URL + '/event_organizers',
                                 headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'organizers' not in response.json()

    def test_get_with_valid_token(self, token):
        response = requests.get(API_URL + '/event_organizers', headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'event_organizers' in results

    def test_post_with_invalid_token(self, sample_user):
        event_organizer = {
            "user_id": sample_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/event_organizers', data=json.dumps(event_organizer),
                                 headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, token, sample_user):
        event_organizer = {
            "user_id": sample_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(API_URL + '/event_organizers', data=json.dumps(event_organizer),
                                 headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 201, 'Status should be Ok, Resource created (201)'
        assert 'Location' in response.headers
        response = response.json()
        assert response['id'] > 0
        EventOrganizer.session.commit()
        event_organizer = EventOrganizer.get_by_id(response['id'])
        assert event_organizer, 'Event organizer created successfully in db'
        EventOrganizer.delete(event_organizer.id)

    def test_delete_with_invalid_token(self):

        response = requests.delete(API_URL + '/event_organizers', data=json.dumps({'ids': []}),
                                   headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token(self, token, organizer_in_db):
        organizer_ids = {'ids': [organizer_in_db.id]}
        response = requests.delete(API_URL + '/event_organizers',  data=json.dumps(organizer_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'

        organizer_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(API_URL + '/event_organizers',  data=json.dumps(organizer_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 207, 'Unable to delete all organizers (207)'
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

        organizer_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(API_URL + '/event_organizers',  data=json.dumps(organizer_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 400, 'Bad Request'
        response = response.json()
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'
