# Std imports
import json
from datetime import datetime

# Third Party
import pytest
import requests
from requests import codes

# App specific imports
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.tests.helper_functions import auth_header, get_headers


class TestOrganizers(object):
    def test_get_with_invalid_token(self):
        """
        Send GET request with invalid token in header and response should be un-authorize access
        """
        response = requests.post(SocialNetworkApiUrl.EVENT_ORGANIZERS,
                                 headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, 'It should be unauthorized (401)'
        assert 'organizers' not in response.json()

    def test_get_with_valid_token(self, token_first):
        """
        Send GET request with valid token in header and id. Response should be 200
        """
        response = requests.get(SocialNetworkApiUrl.EVENT_ORGANIZERS, headers=auth_header(token_first))
        logger.info(response.text)
        # to most messages we placed on RHS of asserts
        assert response.status_code == codes.OK, response.text
        results = response.json()
        assert 'event_organizers' in results

    def test_post_with_invalid_token(self, user_first):
        """
        Send POST request with invalid token in header and response should be 401 (un-authorize)
        """
        event_organizer = {
            "user_id": user_first['id'],
            "name": "Test Organizer",
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(event_organizer),
                                 headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, response.text

    @pytest.mark.skipif(True, reason='TODO: Modify following tests when separate URLs for Eventbrite')
    def test_post_with_valid_token(self, token_first, user_first):
        """
        Send POST request with valid event organizer data and response should be 201 (id in response content)
        """
        event_organizer = {
            "user_id": user_first['id'],
            "name": datetime.now().strftime('%Y%m%dT%H%M%S'),
            "email": "testemail@gmail.com",
            "about": "He is a testing engineer"
        }
        response = requests.post(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(event_organizer),
                                 headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.CREATED, 'Status should be Ok, Resource created (201)'
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
        """
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps({'ids': []}),
                                   headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, response.text

    def test_delete_with_invalid_id(self, token_first):
        """
        Send DELETE request with invalid organizer ids and response should be 207 (not all deleted)
        """
        organizer_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(organizer_ids),
                                   headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.MULTI_STATUS, response.text
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

    def test_delete_with_valid_token(self, token_first, organizer_in_db):
        """
        Send DELETE request with invalid data (i.e. send organizer_ids in other data type than list)
        """
        organizer_ids = {'ids': [organizer_in_db['id']]}
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(organizer_ids),
                                   headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, response.text

        organizer_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(SocialNetworkApiUrl.EVENT_ORGANIZERS, data=json.dumps(organizer_ids),
                                   headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.BAD, response.text
        response = response.json()
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'
