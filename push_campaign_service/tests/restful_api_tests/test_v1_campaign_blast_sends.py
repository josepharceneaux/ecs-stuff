"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import sys

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test

URL = PushCampaignApiUrl.BLAST_SENDS


class TestCampaignBlastSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends [GET]

    def test_get_campaign_blast_sends_with_invalid_token(self, campaign_in_db, campaign_blast):
        """
        We are getting campaign blast's sends with invalid token and it will
        raise Unauthorized error 401
        :param campaign_in_db: campaign object
        :param campaign_blast: campaign blast object
        :return:
        """
        unauthorize_test('get', URL % (campaign_in_db['id'], campaign_blast['id']),
                         'invalid_token')

    def test_get_campaign_blast_sends_with_invalid_campaign_id(self, token_first, campaign_blast):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_blast: campaign blast object
        :return:
        """
        invalid_campaign_id = sys.maxint
        response = send_request('get', URL
                                    % (invalid_campaign_id, campaign_blast['id']), token_first)
        assert response.status_code == NOT_FOUND

    def test_get_campaign_blast_sends_with_invalid_blast_id(self, token_first, campaign_in_db):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :return:
        """
        invalid_blast_id = sys.maxint
        response = send_request('get', URL
                                    % (campaign_in_db['id'], invalid_blast_id), token_first)
        assert response.status_code == NOT_FOUND

    def test_get_campaign_blast_sends(self, token_first, campaign_in_db,
                                      campaign_blast):
        """
        Try to get sends with a valid campaign and blast id and we hope that we will get
        200 (OK) response.
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param campaign_blast: campaign blast object
        :return:
        """
        # 200 case: Got Campaign Sends successfully
        response = send_request('get', URL
                                % (campaign_in_db['id'], campaign_blast['id']), token_first)
        assert response.status_code == OK
        response = response.json()
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == 1
        assert len(response['sends']) == 1
