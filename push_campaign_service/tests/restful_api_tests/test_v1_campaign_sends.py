"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/sends

In these tests, we will try to get a campaign's sends
in different scenarios like:

Get Campaign's Sends: /v1/push-campaigns/:id/sends [GET]
    - with invalid token
    - with non existing campaign
    - with invalid blast id
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
    - with user token that created that campaign (200)
"""
# Builtin imports
import sys

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.utils.test_utils import HttpStatus
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.SENDS


class TestCampaignSends(object):

    # Test URL: /v1/push-campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_sends_with_invalid_token(self, campaign_in_db):
        """
        Try to get a campaign send with invalid token, we are expecting that we will get
        Unauthorized (401) error
        :param campaign_in_db: campaign object
        :return:
        """
        campaign_id = campaign_in_db['id']
        get_campaign_sends(campaign_id, 'invalid_token', expected_status=(HttpStatus.UNAUTHORIZED,))

    def test_get_campaign_sends_for_non_existing_campaign(self, token_first):
        """
        Test that accessing campaign sends of a non existing campaign
        raises ResourceNotFound 404 error
        :param token_first: auth token
        :return:
        """
        # 404 Case, Campaign not found
        invalid_id = sys.maxint
        get_campaign_sends(invalid_id, token_first, expected_status=(HttpStatus.NOT_FOUND,))

#TODO: IMO campaign_blast is not needed here
    def test_get_campaign_sends_without_ownership(self, token_second, campaign_in_db, campaign_blasts):
        """
        Test that accessing campaign sends of a campaign created by other user will
        raise Forbidden 403 error
        :param token_second: auth token of another valid user from different domain
        :return:
        """
        # 403 Case, Not authorized
        get_campaign_sends(campaign_in_db['id'], token_second, expected_status=(HttpStatus.FORBIDDEN,))

    def test_get_campaign_sends_with_diff_user_from_same_domain(self, token_same_domain,
                                                                campaign_in_db, campaign_blasts):
        """
        Test that accessing campaign sends of a campaign created by other user but domain is
        same , so current user can access campaign sends
        :param token_same_domain: auth token of another valid user from different domain
        :return:
        """
        # 403 Case, Not authorized
        get_campaign_sends(campaign_in_db['id'], token_same_domain, expected_status=(HttpStatus.OK,))

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
        response = get_campaign_sends(campaign_in_db['id'], token_first,
                                      expected_status=(HttpStatus.OK,))
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == len(campaign_blasts)
        assert len(response['sends']) == len(campaign_blasts)
