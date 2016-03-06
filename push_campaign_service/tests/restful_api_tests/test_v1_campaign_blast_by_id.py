"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/blasts/:id

In these tests, we will try to get a campaign's blast by Id
in different scenarios like:

Get Campaign's Blast: /v1/push-campaigns/:id/blasts/:id [GET]
    - with invalid token
    - with non existing campaign
    - with invalid blast id
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
"""
# Application specific imports
import sys

from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.utils.test_utils import HttpStatus
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.BLAST


class TestCampaignBlastById(object):

    # Test URL: /v1/push-campaigns/<int:campaign_id>/blasts/<int:blast_id> [GET]
    def test_get_campaign_blast_with_invalid_token(self, campaign_blast, campaign_in_db):
        """
        We are getting campaign blast with invalid token and it will raise Unauthorized error 401
        :param campaign_blast: campaign blast object
        :param campaign_in_db: campaign object
        :return:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast(blast_id, campaign_id, 'invalid_token',
                  expected_status=(HttpStatus.UNAUTHORIZED,))

    def test_get_campaign_blast_with_non_existing_campaign(self, token_first, campaign_blast,
                                                           campaign_in_db):
        """
        We are trying to get a blast of a campaign that does not exist,
        we are expecting ResourceNotFound error 404
        :param token_first: auth token
        :param campaign_blast: campaign blast object
        :param campaign_in_db: campaign object
        :return:
        """
        # 404 Case, Campaign not found
        blast_id = campaign_blast['id']
        invalid_campaign_id = sys.maxint
        get_blast(blast_id, invalid_campaign_id, token_first,
                  expected_status=(HttpStatus.NOT_FOUND,))

    def test_get_campaign_blast_with_invalid_blast_id(self, token_first, campaign_blast,
                                                      campaign_in_db):
        """
        Try to get a valid campaign's blast with invalid blast id,
        and we are expecting ResourceNotFound error here
        :param token_first: auth token
        :param campaign_blast: campaign blast object
        :param campaign_in_db: campaign object
        :return:
        """
        # 404 Case, Blast not found
        invalid_blast_id = sys.maxint
        campaign_id = campaign_in_db['id']
        get_blast(invalid_blast_id, campaign_id, token_first,
                  expected_status=(HttpStatus.NOT_FOUND,))

    def test_get_campaign_blast_from_diff_domain(self, token_second, campaign_blast, campaign_in_db):
        """
        We are trying to get a valid campaign blast but user is from different domain,
        so we are expecting 403 status code.
        :param token_second: auth token
        :param campaign_blast: campaign blast object
        :param campaign_in_db: campaign object
        :return:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast(blast_id, campaign_id, token_second,
                  expected_status=(HttpStatus.FORBIDDEN,))

    def test_get_campaign_blast(self, token_first, campaign_blast, campaign_in_db):
        # 200 case: Campaign Blast successfully
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        response = get_blast(blast_id, campaign_id, token_first,
                             expected_status=(HttpStatus.OK,))
        blast = response['blast']
        assert blast['sends'] == campaign_blast['sends']
        assert blast['clicks'] == campaign_blast['clicks']
        assert blast['id'] == campaign_blast['id']

    def test_get_campaign_blast_with_same_domain_user(self, token_same_domain,
                                                      campaign_blast, campaign_in_db):
        # 200 case: Campaign Blast successfully
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        response = get_blast(blast_id, campaign_id, token_same_domain,
                             expected_status=(HttpStatus.OK,))
        blast = response['blast']
        assert blast['sends'] == campaign_blast['sends']
        assert blast['clicks'] == campaign_blast['clicks']
        assert blast['id'] == campaign_blast['id']
