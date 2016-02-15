# Std imports
import json
import requests

# Application specific imports
from social_network_service.common.models.venue import Venue
from social_network_service.common.utils.models_utils import get_by_id
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.tests.helper_functions import auth_header, get_headers


class TestVenues:

    def test_get_with_invalid_token(self):
        """
        Send POST request with invalid_token in header and response should be 401 (unauthorize)
        :return:
        """
        response = requests.post(SocialNetworkApiUrl.VENUES, headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'venues' not in response.json()

    def test_get_with_valid_token(self, token):
        """
        Send GET request to venues and response should be 200.
        :param token:
        :return:
        """
        response = requests.get(SocialNetworkApiUrl.VENUES, headers=auth_header(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'
        results = response.json()
        assert 'venues' in results

    def test_post_with_invalid_token(self):
        """
        Send POST request to create venue endpoint with invalid token in header and response should be 401 unauthorize
        :return:
        """
        response = requests.post(SocialNetworkApiUrl.VENUES, headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token(self, token):
        """
        Send POST request with valid venue data to create venue endpoint and response should be 201
        :param token:
        :return:
        """
        venue = {
            "social_network_id": 18,
            "zip_code": "54600",
            "address_line_2": "H# 163, Block A",
            "address_line_1": "New Muslim Town",
            "latitude": 0,
            "longitude": 0,
            "state": "CA",
            "city": "Lahore",
            "country": "Pakistan"
        }
        response = requests.post(SocialNetworkApiUrl.VENUES, data=json.dumps(venue),
                                 headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 201, 'Status should be Ok, Resource created (201)'
        assert 'Location' in response.headers
        response = response.json()
        assert response['id'] > 0
        Venue.session.commit()
        venue = Venue.get_by_id(response['id'])
        assert venue, 'Venue created successfully in db'
        Venue.delete(venue.id)

    def test_delete_with_invalid_token(self):
        """
        Send DELETE request to delete venues endpoint using invalid token in header. response should be unauthorize (401)
        :return:
        """
        response = requests.delete(SocialNetworkApiUrl.VENUES, data=json.dumps({'ids': []}),
                                   headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_deletew_invalid_values(self, token):
        """
        Send DELETE request with invalid values in ids(post data) and response should be 207
        :param token:
        :return:
        """
        venue_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(SocialNetworkApiUrl.VENUES,  data=json.dumps(venue_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 207, 'Unable to delete all venues (207)'
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

    def test_delete_with_valid_token(self, token, venue_in_db):
        """
        Create venue using endpoint and send DELETE that venue using id
        :param token:
        :param venue_in_db:
        :return:
        """
        venue_ids = {'ids': [venue_in_db.id]}
        response = requests.delete(SocialNetworkApiUrl.VENUES,  data=json.dumps(venue_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 200, 'Status should be Ok (200)'

        venue_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(SocialNetworkApiUrl.VENUES,  data=json.dumps(venue_ids),
                                   headers=get_headers(token))
        logger.info(response.text)
        assert response.status_code == 400, 'Bad Request'
        response = response.json()
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'

