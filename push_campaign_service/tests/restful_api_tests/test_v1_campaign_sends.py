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
            unauthorize_test('get', URL % campaign_in_db.id, 'invalid_token')

    def test_get_campaign_sends_for_non_existing_campaign(self, token):
        """
        Test that accessing campaign sends of a non existing campaign
        raises ResourceNotFound 404 error
        :param token: auth token
        :return:
        """
        # 404 Case, Campaign not found
        invalid_id = get_non_existing_id(PushCampaign)
        response = send_request('get', URL % invalid_id, token)
        assert response.status_code == NOT_FOUND, 'Resource should not be found'

    def test_get_campaign_sends_without_ownership(self, token2, campaign_in_db, test_smartlist,
                                campaign_blasts_count):
        """
        Test that accessing campaign sends of a campaign created by other user will
        raise Forbidden 403 error
        :param token2: auth token of another valid user
        :return:
        """
        # 403 Case, Not authorized
        response = send_request('get', URL % campaign_in_db.id, token2)
        assert response.status_code == FORBIDDEN

    def test_get_campaign_sends(self, token, campaign_in_db, test_smartlist,
                                campaign_blasts_count):
        """
        Test success case. Get sends of a campaign with valid token, valid campaign id,
        campaign with some sends. It should return OK response (200 status code)
        :param token:
        :param campaign_in_db: push campaign creaed by fixture
        :param test_smartlist: associated smarlist with this campaign
        :param campaign_blasts_count: blasts count for above campaign created in fixture
        :return:
        """
        # Wait for campaigns to be sent
        time.sleep(2 * SLEEP_TIME)

        # 200 case: Got Campaign Sends successfully
        response = send_request('get', URL % campaign_in_db.id, token)
        assert response.status_code == OK, 'Could not get campaign sends info'
        response = response.json()
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == campaign_blasts_count
        assert len(response['sends']) == campaign_blasts_count
