"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import sys
import time

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test, send_request

URL = PushCampaignApiUrl.SEND


class TestSendCampaign(object):
    # Send a campaign
    # URL: /v1/campaigns/<int:campaign_id>/send [POST]
    def test_send_campaign_with_invalid_token(self, campaign_in_db):
        """
        Try to send a campaign with an invalid token, API should raise Unauthorized error
        :param campaign_in_db: campaign object
        :return:
        """
        unauthorize_test('post', URL % campaign_in_db['id'], 'invalid_token')

    def test_send_campaign_with_non_existing_campaign(self, token_first):
        """
        Try to send a campaign that does not exist, API should raise ResourceNotFound (404) error
        :param token_first: auth token
        :return:
        """
        # 404 case. Send a non existing campaign id
        invalid_id = sys.maxint
        send_campaign(invalid_id, token_first, expected_status=(NOT_FOUND,))

    def test_send_a_camapign(self, token_first, campaign_in_db, smartlist_first):
        """
        We will try to send a campaign and we are expecting 200 response
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist object
        :return:
        """
        # 200 case: Campaign Sent successfully
        send_campaign(campaign_in_db['id'], token_first, expected_status=(OK,))

        # Wait for 20 seconds to run celery which will send campaign and creates blast
        time.sleep(2 * SLEEP_TIME)
        response = get_blasts(campaign_in_db['id'], token_first, expected_status=(OK,))
        blasts = response['blasts']
        assert len(blasts) == 1
        assert blasts[0]['sends'] == 1

    def test_send_camapign_with_same_domain(self, token_same_domain, campaign_in_db):
        """
        User in same domain can send a campaign
        We are expecting 200 status here.
        :param token_same_domain: token for a user that is not owner but in same domain
        :param campaign_in_db: campaign in same domain but created by different user in same domain
        :return:
        """
        # 200 case: Campaign Sent successfully
        send_campaign(campaign_in_db['id'], token_same_domain, expected_status=(OK,))

        # Wait for 20 seconds to run celery which will send campaign and creates blast
        time.sleep(2 * SLEEP_TIME)
        response = get_blasts(campaign_in_db['id'], token_same_domain, expected_status=(OK,))
        blasts = response['blasts']
        assert len(blasts) == 1
        assert blasts[0]['sends'] == 1

    def test_send_camapign_with_diff_domain(self, token_second, campaign_in_db):
        # try to send a campaign with different domain, we should get 403 error, i.e. user
        # is not allowed to send this campaign
        send_campaign(campaign_in_db['id'], token_second, expected_status=(FORBIDDEN,))

    def test_campaign_send_with_multiple_smartlists(self, token_first,
                                                    campaign_in_db_multiple_smartlists):
        """
        - This tests the endpoint /v1/campaigns/:id/send

        User auth token_first is valid, campaign has one smart list associated. Smartlist has one
        candidate.
        :return:
        """
        campaign_id = campaign_in_db_multiple_smartlists['id']
        send_campaign(campaign_id, token_first, expected_status=(OK,))
        time.sleep(SLEEP_TIME)
        # There should be only one blast for this campaign
        response = get_blasts(campaign_id, token_first, expected_status=(OK,))
        blasts = response['blasts']
        assert len(blasts) == 1
        assert blasts[0]['sends'] == 2
