"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
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
        unauthorize_test('post', URL % campaign_in_db['id'], 'invalid_token')

    def test_send_campaign_with_non_existing_campaign(self, token_first):
        # 404 case. Send a non existing campaign id
        invalid_id = 99999999999999999999999;
        response = send_request('post', URL % invalid_id, token_first)
        assert response.status_code == NOT_FOUND, 'Push campaign should not exists with this id'

    def test_send_a_camapign(self, token_first, campaign_in_db, smartlist_first):
        # 200 case: Campaign Sent successfully
        response = send_request('post', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK, 'Push campaign has not been sent'
        response = response.json()
        assert response['message'] == 'Campaign(id:%s) is being sent to candidates' \
                                      % campaign_in_db['id']

        # Wait for 20 seconds to run celery which will send campaign and creates blast
        time.sleep(2 * SLEEP_TIME)
        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
        assert response.status_code == 200
        blasts = response.json()['blasts']
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
        response = send_request('post', URL % campaign_in_db['id'], token_same_domain)
        assert response.status_code == OK, 'Push campaign has not been sent'

        # Wait for 20 seconds to run celery which will send campaign and creates blast
        time.sleep(2 * SLEEP_TIME)
        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'],
                                token_same_domain)
        assert response.status_code == 200
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        assert blasts[0]['sends'] == 1

    def test_send_camapign_with_diff_domain(self, token_second, campaign_in_db):
        # try to send a campaign with different domain, we should get 403 error, i.e. user
        # is not allowed to send this campaign
        response = send_request('post', URL % campaign_in_db['id'], token_second)
        assert response.status_code == 403

    def test_campaign_send_with_multiple_smartlists(
            self, token_first, campaign_in_db_multiple_smartlists):
        """
        - This tests the endpoint /v1/campaigns/:id/send

        User auth token_first is valid, campaign has one smart list associated. Smartlist has one
        candidate.
        :return:
        """
        response = send_request('post', URL % campaign_in_db_multiple_smartlists['id'], token_first)
        assert response.status_code == OK, 'Push campaign has not been sent'

        time.sleep(SLEEP_TIME)
        # There should be only one blast for this campaign
        response = send_request('get', PushCampaignApiUrl.BLASTS
                                % campaign_in_db_multiple_smartlists['id'], token_first)
        assert response.status_code == 200
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        assert blasts[0]['sends'] == 2
