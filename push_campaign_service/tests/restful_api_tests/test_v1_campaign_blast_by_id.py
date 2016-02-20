"""
This module contains tests related to Push Campaign RESTful API endpoint
/v1/campaigns/:id/blasts/:id
"""
# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test

URL = PushCampaignApiUrl.BLAST


class TestCampaignBlastById(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id> [GET]
    def test_get_campaign_blast_with_invalid_token(self, campaign_blast, campaign_in_db):

        unauthorize_test('get', URL % (campaign_in_db['id'], campaign_blast['id']),
                         'invalid_token')

    def test_get_campaign_blast_with_non_existing_campaign(self, token_first, campaign_blast, campaign_in_db):
        # 404 Case, Campaign not found
        invalid_campaign_id = campaign_in_db['id'] + 10000
        response = send_request('get', URL
                                % (invalid_campaign_id, campaign_blast['id']), token_first)
        assert response.status_code == NOT_FOUND

    def test_get_campaign_blast_with_invalid_blast_id(self, token_first, campaign_blast, campaign_in_db):
        # 404 Case, Blast not found
        invalid_blast_id = campaign_blast['id'] + 10000
        response = send_request('get', URL
                                % (campaign_in_db['id'], invalid_blast_id), token_first)
        assert response.status_code == NOT_FOUND

    def test_get_campaign_blast_without_ownership(self, token_second, campaign_blast, campaign_in_db):
        # 403 Case, User is not owner of campaign
        response = send_request('get', URL
                                % (campaign_in_db['id'], campaign_blast['id']), token_second)
        assert response.status_code == FORBIDDEN

    def test_get_campaign_blast(self, token_first, campaign_blast, campaign_in_db):
        # 200 case: Campaign Blast successfully
        response = send_request('get', URL % (campaign_in_db['id'], campaign_blast['id']),
                                token_first)
        assert response.status_code == OK, 'Could not get campaign blasts info'
        response = response.json()['blast']
        assert response['sends'] == campaign_blast['sends']
        assert response['clicks'] == campaign_blast['clicks']
        assert response['id'] == campaign_blast['id']
