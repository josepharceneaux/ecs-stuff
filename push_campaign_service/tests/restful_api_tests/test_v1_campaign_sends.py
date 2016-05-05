"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/sends

In these tests, we will try to get a campaign's sends
in different scenarios like:

Get Campaign's Sends: /v1/push-campaigns/:id/sends [GET]
    - with invalid token
    - with non existing campaign
    - with invalid blast id
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
    - with user token that created that campaign (200)
"""
# Builtin imports
import sys
import time

# 3rd party imports
from redo import retry
from requests import codes

# Application specific imports
from push_campaign_service.tests.test_utilities import get_campaign_sends, SLEEP_TIME
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.api_utils import MAX_PAGE_SIZE

URL = PushCampaignApiUrl.SENDS


class TestCampaignSends(object):

    # Test URL: /v1/push-campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_sends_with_invalid_token(self, campaign_in_db):
        """
        Try to get a campaign send with invalid token, we are expecting that we will get
        Unauthorized (401) error
        :param campaign_in_db: campaign object
        """
        campaign_id = campaign_in_db['id']
        get_campaign_sends(campaign_id, 'invalid_token', expected_status=(codes.UNAUTHORIZED,))

    def test_get_campaign_sends_for_non_existing_campaign(self, token_first):
        """
        Test that accessing campaign sends of a non existing campaign
        raises ResourceNotFound 404 error
        :param token_first: auth token
        """
        # 404 Case, Campaign not found
        invalid_id = sys.maxint
        get_campaign_sends(invalid_id, token_first, expected_status=(codes.NOT_FOUND,))

    def test_get_campaign_sends_from_diff_domain(self, token_second, campaign_in_db):
        """
        Test that accessing campaign sends of a campaign created by other user will
        raise Forbidden 403 error
        :param token_second: auth token of another valid user from different domain
        :param campaign_in_db: campaign object
        """
        # 403 Case, Not authorized
        get_campaign_sends(campaign_in_db['id'], token_second, expected_status=(codes.FORBIDDEN,))

    def test_get_campaign_sends_with_diff_user_from_same_domain(self, token_same_domain, candidate_first,
                                                                candidate_device_first, campaign_in_db, campaign_blasts):
        """
        Test that accessing campaign sends of a campaign created by other user but domain is
        same , so current user can access campaign sends
        :param token_same_domain: auth token of another valid user from different domain
        """
        get_campaign_sends(campaign_in_db['id'], token_same_domain, expected_status=(codes.OK,))

    def test_get_campaign_sends_paginated(self, token_first, candidate_first, candidate_device_first,
                                          campaign_in_db, campaign_blasts_pagination):
        """
        Test success case. Get sends of a campaign with valid token, valid campaign id,
        campaign with some sends. It should return OK response (200 status code)
        :param token_first: auth token
        :param campaign_in_db: push campaign created by fixture
        :param campaign_blasts_pagination: blasts count
        """
        campaign_id = campaign_in_db['id']
        blasts_count = campaign_blasts_pagination
        per_page = blasts_count - 5
        retry(get_campaign_sends, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
              args=(campaign_id, token_first), kwargs={'per_page': per_page, 'count': per_page})

        retry(get_campaign_sends, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
              args=(campaign_id, token_first),
              kwargs={'page': 2, 'per_page': per_page, 'count': (blasts_count - per_page)})

        per_page = blasts_count
        retry(get_campaign_sends, sleeptime=3, max_sleeptime=60, retry_exceptions=(AssertionError,),
              args=(campaign_id, token_first), kwargs={'per_page': per_page, 'count': blasts_count})

        response = get_campaign_sends(campaign_id, token_first, page=2, per_page=20,
                                      expected_status=(codes.OK,))
        assert len(response['sends']) == 0

        # set page size greater than max allowed page size, 400 is expected
        per_page = MAX_PAGE_SIZE + 1
        get_campaign_sends(campaign_id, token_first, per_page=per_page,
                           expected_status=(codes.BAD_REQUEST,))


