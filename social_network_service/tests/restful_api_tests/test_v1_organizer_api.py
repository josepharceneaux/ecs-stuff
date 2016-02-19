# Std imports
import json

import requests
# App specific imports
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.tests.helper_functions import auth_header, get_headers
from social_network_service.common.tests.conftest import first_group, domain_first, sample_user


class TestOrganizers:

    def test_get_with_invalid_token(self):
        """
        Send GET request with invalid token in header and response should be unauthorize access
        :return:
        """
        response = requests.post(SocialNetworkApiUrl.EVENT_ORGANIZERS,
                                 headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'organizers' not in response.json()

    def test_get_with_valid_token(self, token):
        """
        Send GET request with valid token in header and id. Response should be 200
        :param token:
        :return:
        """
        response = requests.get(SocialNetworkApiUrl.EVENT_ORGANIZERS, headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'event_organizers' in results

    def test_post_with_invalid_token(self, sample_user):
        """
        Send POST request with invalid token in header and response should be 401 (unauthorize)
        :param sample_user:
        :return:
        """
        event_organizer = {
            "user_id": sample_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(event_organizer),
                                 headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, token, sample_user):
        """
        Send POST request with valid event organizer data and response should be 201 (id in response content)
        :param token:
        :param sample_user:
        :return:
        """
        event_organizer = {
            "user_id": sample_user.id,
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(event_organizer),
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
        """
        Send DELETE request with invalid token in header and response should be 401 (unauthorize)
        :return:
        """
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps({'ids': []}),
                                   headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_invalid_id(self, token):
        """
        Send DELETE request with invalid organizer ids and response should be 207 (not all deleted)
        :param token:
        :return:
        """
        organizer_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS,  data=json.dumps(organizer_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 207, 'Unable to delete all organizers (207)'
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

    def test_delete_with_valid_token(self, token, organizer_in_db):
        """
        Send DELETE request with invalid data (i.e. send organizer_ids in other data type than list)
        :param token:
        :param organizer_in_db:
        :return:
        """
        organizer_ids = {'ids': [organizer_in_db.id]}
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS,  data=json.dumps(organizer_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'

        organizer_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS,  data=json.dumps(organizer_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 400, 'Bad Request'
        response = response.json()
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'
