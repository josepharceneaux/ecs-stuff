"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/blasts

In these tests, we will try to get a campaign's blasts
in different scenarios like:

Get Campaign's Blast: /v1/push-campaigns/:id/blasts [GET]
    - with invalid token
    - with non existing campaign
    - with valid campaign id (200)
"""
# Standard imports
import sys

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.BLASTS


class TestCampaignBlasts(object):

    # Test URL: /v1/push-campaigns/<int:campaign_id>/blasts [GET]
    def test_get_campaign_blasts_with_invalid_token(self, campaign_in_db):
        """
        We are getting campaign blasts with invalid token and it will
        raise Unauthorized error 401
        :param campaign_in_db: campaign object
        :return:
        """
        campaign_id = campaign_in_db['id']
        get_blasts(campaign_id, 'invalid_token', expected_status=(401,))

    def test_get_campaign_blasts_with_invalid_campaign_id(self, token_first):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :return:
        """
        invalid_campaign_id = sys.maxint
        get_blasts(invalid_campaign_id, token_first, expected_status=(NOT_FOUND,))

    def test_get_campaign_blasts(self, token_first, campaign_in_db, campaign_blasts):
        """
        Try to get blasts of a valid campaign and it should return OK response
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param campaign_blasts: campaign blast list
        :return:
        """
        # 200 case: Campaign Blast successfully
        response = send_request('get', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK, 'Could not get campaign blasts info'
        response = get_blasts(campaign_in_db['id'], token_first)
        assert response['count'] == len(campaign_blasts)
        assert len(response['blasts']) == len(campaign_blasts)
