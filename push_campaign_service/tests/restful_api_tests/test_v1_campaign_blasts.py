"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Standard imports
import sys

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test

URL = PushCampaignApiUrl.BLASTS


class TestCampaignBlasts(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts [GET]
    def test_get_campaign_blasts_with_invalid_token(self, campaign_in_db):
        """
        We are getting campaign blasts with invalid token and it will
        raise Unauthorized error 401
        :param campaign_in_db: campaign object
        :return:
        """
        unauthorize_test('get', URL % campaign_in_db['id'], 'invalid_token')

    def test_get_campaign_blasts_with_invalid_campaign_id(self, token_first):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_blast: campaign blast object
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
