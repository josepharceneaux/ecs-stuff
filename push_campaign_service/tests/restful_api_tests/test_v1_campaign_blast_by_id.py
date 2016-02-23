"""
This module contains tests related to Push Campaign RESTful API endpoint
/v1/campaigns/:id/blasts/:id
"""
# Application specific imports
import sys

from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test

URL = PushCampaignApiUrl.BLAST


class TestCampaignBlastById(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id> [GET]
    def test_get_campaign_blast_with_invalid_token(self, campaign_blast, campaign_in_db):
        """
        We are getting campaign blast with invalid token and it will raise Unauthorized error 401
        :param campaign_blast: campaign blast object
        :param campaign_in_db: campaign object
        :return:
        """
        unauthorize_test('get', URL % (campaign_in_db['id'], campaign_blast['id']),
                         'invalid_token')

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
        invalid_campaign_id = campaign_in_db['id'] + 10000
        get_blast(blast_id, invalid_campaign_id, token_first, expected_status=(NOT_FOUND,))

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
        get_blast(invalid_blast_id, campaign_id, token_first, expected_status=(NOT_FOUND,))

    def test_get_campaign_blast_without_ownership(self, token_second, campaign_blast,
                                                  campaign_in_db):
        """
        We are trying to get a valid campaign blast but user
        :param token_second: auth token
        :param campaign_blast: campaign blast object
        :param campaign_in_db: campaign object
        :return:
        """
        # 403 Case, User is not owner of campaign
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast(blast_id, campaign_id, token_second, expected_status=(FORBIDDEN,))

    def test_get_campaign_blast(self, token_first, campaign_blast, campaign_in_db):
        # 200 case: Campaign Blast successfully
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        response = get_blast(blast_id, campaign_id, token_first, expected_status=(OK,))
        blast = response['blast']
        assert blast['sends'] == campaign_blast['sends']
        assert blast['clicks'] == campaign_blast['clicks']
        assert blast['id'] == campaign_blast['id']

    def test_get_campaign_blast_with_same_doamin_user(self, token_same_domain,
                                                      campaign_blast, campaign_in_db):
        # 200 case: Campaign Blast successfully
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        response = get_blast(blast_id, campaign_id, token_same_domain, expected_status=(OK,))
        blast = response['blast']
        assert blast['sends'] == campaign_blast['sends']
        assert blast['clicks'] == campaign_blast['clicks']
        assert blast['id'] == campaign_blast['id']
