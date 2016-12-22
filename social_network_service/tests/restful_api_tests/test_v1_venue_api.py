# Std imports
import json

# Third Party
import pytest
import requests
from requests import codes

# Application specific imports
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.venue import Venue
from social_network_service.modules.constants import EVENTBRITE
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.tests.conftest import EVENTBRITE_CONFIG
from social_network_service.tests.helper_functions import auth_header, get_headers, match_venue_fields


class TestVenues(object):
    def test_get_with_invalid_token(self):
        """
        Send POST request with invalid_token in header and response should be 401 (unauthorized)
        """
        response = requests.post(SocialNetworkApiUrl.VENUES, headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, 'It should be unauthorized (401)'
        assert 'venues' not in response.json()

    def test_get_with_valid_token(self, token_first):
        """
        Send GET request to venues and response should be 200.
        """
        response = requests.get(SocialNetworkApiUrl.VENUES, headers=auth_header(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        results = response.json()
        assert 'venues' in results

    def test_match_venue_fileds(self, token_first, venue_in_db_second):
        """
        Creates venue for social network events, send GET request to venues and test if expected
        fields exist in response from api.
        """
        response = requests.get(SocialNetworkApiUrl.VENUE % venue_in_db_second['id'],
                                headers=auth_header(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'
        results = response.json()
        assert 'venue' in results
        assert len(results) == 1
        match_venue_fields(results['venue'])

    def test_post_with_invalid_token(self):
        """
        Send POST request to create venue endpoint with invalid token in header and response should be 401 unauthorized
        """
        response = requests.post(SocialNetworkApiUrl.VENUES, headers=auth_header('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, 'It should be unauthorized (401)'

    @pytest.mark.skipif(EVENTBRITE_CONFIG['skip'], reason=EVENTBRITE_CONFIG['reason'])
    def test_post_with_valid_token(self, token_first):
        """
        Send POST request with valid venue data to create venue endpoint and response should be 201
        """
        social_network = SocialNetwork.get_by_name(EVENTBRITE.title())
        venue = {
            "social_network_id": social_network.id,
            "zip_code": "54600",
            "address_line_2": "H# 163, Block A",
            "address_line_1": "New Muslim Town",
            "latitude": 0,
            "longitude": 0,
            "state": "CA",
            "city": "Lahore",
            "country": "Pakistan"
        }
        response = requests.post(SocialNetworkApiUrl.VENUES, data=json.dumps(venue), headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.CREATED, 'Status should be Ok, Resource created (201)'
        assert 'Location' in response.headers
        response = response.json()
        assert response['id'] > 0
        Venue.session.commit()
        venue = Venue.get_by_id(response['id'])
        assert venue, 'Venue created successfully in db'
        Venue.delete(venue.id)

    def test_delete_with_invalid_token(self):
        """
        Send DELETE request to delete venues endpoint using invalid token in header. response should be
        unauthorized (401)
        """
        response = requests.delete(SocialNetworkApiUrl.VENUES, data=json.dumps({'ids': []}),
                                   headers=get_headers('invalid_token'))
        logger.info(response.text)
        assert response.status_code == codes.UNAUTHORIZED, 'It should be unauthorized (401)'

    def test_delete_with_invalid_values(self, token_first):
        """
        Send DELETE request with invalid values in ids(post data) and response should be 207
        """
        venue_ids = {'ids': [-1]}  # event id which does not exists, test 207 status
        response = requests.delete(SocialNetworkApiUrl.VENUES, data=json.dumps(venue_ids),
                                   headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.MULTI_STATUS, 'Unable to delete all venues (207)'
        response = response.json()
        assert 'deleted' in response and len(response['deleted']) == 0
        assert 'not_deleted' in response and len(response['not_deleted']) == 1
        assert 'message' in response

    def test_delete_with_valid_token(self, token_first, venue_in_db_second):
        """
        Create venue using endpoint and send DELETE that venue using id
        """
        venue_ids = {'ids': [venue_in_db_second['id']]}
        response = requests.delete(SocialNetworkApiUrl.VENUES, data=json.dumps(venue_ids),
                                   headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.OK, 'Status should be Ok (200)'

        venue_ids = {'ids': -1}  # invalid ids format to test 400 status code
        response = requests.delete(SocialNetworkApiUrl.VENUES, data=json.dumps(venue_ids),
                                   headers=get_headers(token_first))
        logger.info(response.text)
        assert response.status_code == codes.BAD, 'Bad Request'
        response = response.json()
        assert 'message' in response['error'] and \
               response['error']['message'] == 'Bad request, include ids as list data'
