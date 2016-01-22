"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl


class TestCampaignSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_send_with_invalid_token(self, campaign_in_db):
            unauthorize_test('get', PushCampaignApiUrl.SENDS % campaign_in_db.id, 'invalid_token')

    def test_get_campaign_sends(self, token, campaign_in_db, test_smartlist,
                                campaign_blasts_count):

        # Wait for campaigns to be sent
        time.sleep(2 * SLEEP_TIME)

        # 404 Case, Campaign not found
        last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
        invalid_id = last_obj.id + 100
        response = send_request('get', PushCampaignApiUrl.SENDS % invalid_id, token)
        assert response.status_code == NOT_FOUND, 'Resource should not be found'
        # 200 case: Got Campaign Sends successfully
        response = send_request('get', PushCampaignApiUrl.SENDS % campaign_in_db.id, token)
        assert response.status_code == OK, 'Could not get campaign sends info'
        response = response.json()
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == campaign_blasts_count
        assert len(response['sends']) == campaign_blasts_count
