"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/send

In these tests, we will try to create, get and delete
push campaigns with different scenarios

Send a Campaign: /v1/push-campaigns/:id/send [POST]
    - with invalid token
    - with non existing campaign id
    - with token for a different user from same domain
    - with token for a different user from different domain
    - with valid token
    - with multiple smartlists associated with campaign
"""
# Builtin imports
import sys

# 3rd party imports
from redo import retry
from requests import codes

# Application specific imports
from push_campaign_service.tests.test_utilities import send_campaign, get_blasts, get_blast_sends
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.SEND


class TestSendCampaign(object):
    # Send a campaign
    # URL: /v1/push-campaigns/<int:campaign_id>/send [POST]
    def test_send_campaign_with_invalid_token(self, campaign_in_db):
        """
        Try to send a campaign with an invalid token, API should raise Unauthorized error
        :param campaign_in_db: campaign object
        """
        send_campaign(campaign_in_db['id'], 'invalid_token',
                      expected_status=(codes.UNAUTHORIZED,))

    def test_send_campaign_with_non_existing_campaign(self, token_first):
        """
        Try to send a campaign that does not exist, API should raise ResourceNotFound (404) error
        :param token_first: auth token
        """
        # 404 case. Send a non existing campaign id
        invalid_id = sys.maxint
        send_campaign(invalid_id, token_first, expected_status=(codes.NOT_FOUND,))

    def test_send_a_camapign_with_valid_data(self, token_first, campaign_in_db,
                                             smartlist_first, candidate_device_first):
        """
        We will try to send a campaign and we are expecting 200 response
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist object
        """
        # 200 case: Campaign Sent successfully
        send_campaign(campaign_in_db['id'], token_first, expected_status=(codes.OK,))

        response = retry(get_blasts, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
                         args=(campaign_in_db['id'], token_first), kwargs={'count': 1})
        blasts = response['blasts']
        blast_id = blasts[0]['id']
        response = retry(get_blast_sends, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
                         args=(blast_id, campaign_in_db['id'], token_first), kwargs={'count': 1})
        assert len(response['sends']) == 1

    def test_send_campaign_with_other_user_in_same_domain(self, token_same_domain, campaign_in_db,
                                                          smartlist_first, candidate_device_first):
        """
        User in same domain can send a campaign
        We are expecting 200 status here.
        :param token_same_domain: token for a user that is not owner but in same domain
        :param campaign_in_db: campaign in same domain but created by different user in same domain
        """
        # 200 case: Campaign Sent successfully
        send_campaign(campaign_in_db['id'], token_same_domain, expected_status=(codes.OK,))

        response = retry(get_blasts, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
                         args=(campaign_in_db['id'], token_same_domain), kwargs={'count': 1})
        blasts = response['blasts']
        blast_id = blasts[0]['id']
        response = retry(get_blast_sends, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
                         args=(blast_id, campaign_in_db['id'], token_same_domain), kwargs={'count': 1})
        assert len(response['sends']) == 1

    def test_send_camapign_with_diff_domain(self, token_second, campaign_in_db):
        # try to send a campaign with different domain, we should get 403 error, i.e. user
        # is not allowed to send this campaign
        send_campaign(campaign_in_db['id'], token_second, expected_status=(codes.FORBIDDEN,))

    def test_campaign_send_with_multiple_smartlists(self, token_first,
                                                    campaign_in_db_multiple_smartlists):
        """
        - This tests the endpoint /v1/push-campaigns/:id/send

        User auth token_first is valid, campaign has one smart list associated. Smartlist has one
        candidate.
        """
        campaign_id = campaign_in_db_multiple_smartlists['id']
        send_campaign(campaign_id, token_first, expected_status=(codes.OK,))
        response = retry(get_blasts, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
                         args=(campaign_id, token_first), kwargs={'count': 1})
        blasts = response['blasts']
        blast_id = blasts[0]['id']
        response = retry(get_blast_sends, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
                         args=(blast_id, campaign_id, token_first), kwargs={'count': 2})
        assert len(response['sends']) == 2

    def test_campaign_send_to_candidate_with_no_device(self, token_first, campaign_in_db):
        """
        In this test, we will send a campaign to a valid candidate (in same domain), but candidate
        has no device associated with him. So no campaign will be sent which will result in
        zero blasts or sends.
        """
        campaign_id = campaign_in_db['id']
        send_campaign(campaign_id, token_first, expected_status=(codes.BAD_REQUEST,))

