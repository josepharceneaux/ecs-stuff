"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl


class TestCampaignBlasts(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts [GET]
    def test_get_campaign_blasts_with_invalid_token(self, campaign_in_db):
        unauthorize_test('get', PushCampaignApiUrl.BLASTS % campaign_in_db.id, 'invalid_token')

    def test_get_campaign_blasts(self, token, campaign_in_db, test_smartlist,
                                 campaign_blasts_count):

        # Wait for campaigns to be sent
        time.sleep(SLEEP_TIME)

        # 404 Case, Campaign not found
        last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
        invalid_id = last_obj.id + 100
        response = send_request('get', PushCampaignApiUrl.BLASTS % invalid_id, token)
        assert response.status_code == NOT_FOUND, 'Resource should not be found'

        # 200 case: Campaign Blast successfully
        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db.id, token)
        assert response.status_code == OK, 'Could not get campaign blasts info'
        response = response.json()
        assert response['count'] == campaign_blasts_count
        assert len(response['blasts']) == campaign_blasts_count