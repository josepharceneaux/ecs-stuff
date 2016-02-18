"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.SENDS


class TestCampaignSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_sends_with_invalid_token(self, campaign_in_db):
            unauthorize_test('get', URL % campaign_in_db['id'], 'invalid_token')

    def test_get_campaign_sends_for_non_existing_campaign(self, token_first, campaign_in_db):
        """
        Test that accessing campaign sends of a non existing campaign
        raises ResourceNotFound 404 error
        :param token: auth token
        :return:
        """
        # 404 Case, Campaign not found
        invalid_id = campaign_in_db['id'] + 10000
        response = send_request('get', URL % invalid_id, token_first)
        assert response.status_code == NOT_FOUND, 'Resource should not be found'

    def test_get_campaign_sends_without_ownership(self, token_second, campaign_in_db, smartlist_first,
                                campaign_blasts):
        """
        Test that accessing campaign sends of a campaign created by other user will
        raise Forbidden 403 error
        :param token2: auth token of another valid user
        :return:
        """
        # 403 Case, Not authorized
        response = send_request('get', URL % campaign_in_db['id'], token_second)
        assert response.status_code == FORBIDDEN

    def test_get_campaign_sends(self, token_first, campaign_in_db, smartlist_first,
                                campaign_blasts):
        """
        Test success case. Get sends of a campaign with valid token, valid campaign id,
        campaign with some sends. It should return OK response (200 status code)
        :param token:
        :param campaign_in_db: push campaign creaed by fixture
        :param smartlist_first: associated smarlist with this campaign
        :param campaign_blasts: blasts for above campaign created in fixture
        :return:
        """

        # 200 case: Got Campaign Sends successfully
        response = send_request('get', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK, 'Could not get campaign sends info'
        response = response.json()
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == len(campaign_blasts)
        assert len(response['sends']) == len(campaign_blasts)
