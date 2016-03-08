"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/blasts/:id/sends

In these tests, we will try to get a campaign blast's sends
in different scenarios like:

Get Blast Sends: /v1/push-campaigns/:id/blasts/:id/sends [GET]
    - with invalid token
    - with non existing campaign
    - with invalid blast id
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
"""
# Builtin imports
import sys

# Application specific imports
from push_campaign_service.common.utils.api_utils import MAX_PAGE_SIZE
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.utils.test_utils import HttpStatus
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.BLAST_SENDS


class TestCampaignBlastSends(object):

    # Test URL: /v1/push-campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends [GET]

    def test_get_campaign_blast_sends_with_invalid_token(self, campaign_in_db, campaign_blast):
        """
        We are getting campaign blast's sends with invalid token and it will
        raise Unauthorized error 401
        :param campaign_in_db: campaign object
        :param campaign_blast: campaign blast object
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast_sends(blast_id, campaign_id, 'invalid_token',
                        expected_status=(HttpStatus.UNAUTHORIZED,))

    def test_get_campaign_blast_sends_with_invalid_campaign_id(self, token_first, campaign_blast):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_blast: campaign blast object
        """
        blast_id = campaign_blast['id']
        campaign_id = sys.maxint
        get_blast_sends(blast_id, campaign_id, token_first,
                        expected_status=(HttpStatus.NOT_FOUND,))

    def test_get_campaign_blast_sends_with_invalid_blast_id(self, token_first, campaign_in_db):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_in_db: campaign object
        """
        invalid_blast_id = sys.maxint
        campaign_id = campaign_in_db['id']
        get_blast_sends(invalid_blast_id, campaign_id, token_first,
                        expected_status=(HttpStatus.NOT_FOUND,))

    def test_get_campaign_blast_sends(self, token_first, campaign_blast):
        """
        Try to get sends with a valid campaign and blast id and we hope that we will get
        200 (OK) response.
        :param token_first: auth token
        :param campaign_blast: campaign blast object
        """
        # 200 case: Got Campaign Sends successfully
        blast_id = campaign_blast['id']
        campaign_id = campaign_blast['campaign_id']
        response = get_blast_sends(blast_id, campaign_id, token_first,
                                   expected_status=(HttpStatus.OK,))
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert len(response['sends']) == 1

        # if page size is greater than maximum allowed page size, it will raise InvalidUsage exception
        per_page = MAX_PAGE_SIZE + 1
        get_blast_sends(blast_id, campaign_id, token_first, per_page=per_page,
                        expected_status=(HttpStatus.INVALID_USAGE,))

    def test_get_campaign_blast_sends_with_user_from_same_domain(self, token_same_domain, campaign_blast):
        """
        Test if a user from same domain can access sends of a campaign blast or not.
        API should allow this user
        :param token_same_domain:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_blast['campaign_id']
        get_blast_sends(blast_id, campaign_id, token_same_domain,
                        expected_status=(HttpStatus.OK,))

    def test_get_campaign_blast_sends_with_user_from_diff_domain(self, token_second, campaign_blast):
        """
        Test if a user from same domain can not access sends of a campaign blast or not.
        API should not allow this user
        :param token_second:
        :param campaign_blast:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_blast['campaign_id']
        get_blast_sends(blast_id, campaign_id, token_second,
                        expected_status=(HttpStatus.FORBIDDEN,))
