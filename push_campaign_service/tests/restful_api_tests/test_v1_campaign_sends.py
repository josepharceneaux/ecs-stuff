"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import sys

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test

URL = PushCampaignApiUrl.SENDS


class TestCampaignSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_sends_with_invalid_token(self, campaign_in_db):
        """
        Try to get a campaign send with invalid token, we are expecting that we will get
        Unauthorized (401) error
        :param campaign_in_db: campaign object
        :return:
        """
        unauthorize_test('get', URL % campaign_in_db['id'], 'invalid_token')

    def test_get_campaign_sends_for_non_existing_campaign(self, token_first):
        """
        Test that accessing campaign sends of a non existing campaign
        raises ResourceNotFound 404 error
        :param token_first: auth token
        :return:
        """
        # 404 Case, Campaign not found
        invalid_id = sys.maxint
        get_campaign_sends(invalid_id, token_first, expected_status=(NOT_FOUND,))

    def test_get_campaign_sends_without_ownership(self, token_second, campaign_in_db,
                                campaign_blasts):
        """
        Test that accessing campaign sends of a campaign created by other user will
        raise Forbidden 403 error
        :param token_second: auth token of another valid user from different domain
        :return:
        """
        # 403 Case, Not authorized
        get_campaign_sends(campaign_in_db['id'], token_second, expected_status=(FORBIDDEN,))

    def test_get_campaign_sends(self, token_first, campaign_in_db, campaign_blasts):
        """
        Test success case. Get sends of a campaign with valid token, valid campaign id,
        campaign with some sends. It should return OK response (200 status code)
        :param token_first: auth token
        :param campaign_in_db: push campaign created by fixture
        :param campaign_blasts: blasts for above campaign created in fixture
        :return:
        """

        # 200 case: Got Campaign Sends successfully
        response = get_campaign_sends(campaign_in_db['id'], token_first, expected_status=(OK,))
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == len(campaign_blasts)
        assert len(response['sends']) == len(campaign_blasts)
