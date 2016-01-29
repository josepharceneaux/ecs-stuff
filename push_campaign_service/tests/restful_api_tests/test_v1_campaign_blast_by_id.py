"""
This module contains tests related to Push Campaign RESTful API endpoint
/v1/campaigns/:id/blasts/:id
"""
# Application specific imports
from push_campaign_service.common.models.push_campaign import PushCampaign, PushCampaignBlast
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.BLAST


class TestCampaignBlastById(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id> [GET]
    def test_get_campaign_blast_with_invalid_token(self, blast_and_camapign_in_db):
        campaign, blast = blast_and_camapign_in_db
        unauthorize_test('get', URL % (campaign.id, blast.id),
                         'invalid_token')

    def test_get_campaign_blast_with_non_existing_campaign(self, token, blast_and_camapign_in_db):
        # 404 Case, Campaign not found
        campaign, blast = blast_and_camapign_in_db
        invalid_campaign_id = get_non_existing_id(PushCampaign)
        response = send_request('get', URL
                                % (invalid_campaign_id, blast.id), token)
        assert response.status_code == NOT_FOUND

    def test_get_campaign_blast_with_invalid_blast_id(self, token, blast_and_camapign_in_db):
        # 404 Case, Blast not found
        campaign, blast = blast_and_camapign_in_db
        invalid_blast_id = get_non_existing_id(PushCampaignBlast)
        response = send_request('get', URL
                                % (campaign.id, invalid_blast_id), token)
        assert response.status_code == NOT_FOUND

    def test_get_campaign_blast_with_without_ownership(self, token2, blast_and_camapign_in_db):
        # 403 Case, User is not owner of campaign
        campaign, blast = blast_and_camapign_in_db
        response = send_request('get', URL
                                % (campaign.id, blast.id), token2)
        assert response.status_code == FORBIDDEN

    def test_get_campaign_blast(self, token, blast_and_camapign_in_db):

        # Wait for campaigns to be sent
        campaign, blast = blast_and_camapign_in_db
        # 200 case: Campaign Blast successfully
        response = send_request('get', URL % (campaign.id, blast.id), token)
        assert response.status_code == OK, 'Could not get campaign blasts info'
        response = response.json()['blast']
        assert response['sends'] == blast.sends
        assert response['clicks'] == blast.clicks
        assert response['id'] == blast.id
