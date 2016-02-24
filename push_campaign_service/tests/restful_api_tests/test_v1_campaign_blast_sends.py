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
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.BLAST_SENDS


class TestCampaignBlastSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends [GET]

    def test_get_campaign_blast_sends_with_invalid_token(self, campaign_in_db, campaign_blast):
        """
        We are getting campaign blast's sends with invalid token and it will
        raise Unauthorized error 401
        :param campaign_in_db: campaign object
        :param campaign_blast: campaign blast object
        :return:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast_sends(blast_id, campaign_id, 'invalid_token', expected_status=(401,))

    def test_get_campaign_blast_sends_with_invalid_campaign_id(self, token_first, campaign_blast):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_blast: campaign blast object
        :return:
        """
        blast_id = campaign_blast['id']
        campaign_id = sys.maxint
        get_blast_sends(blast_id, campaign_id, token_first, expected_status=(NOT_FOUND,))

    def test_get_campaign_blast_sends_with_invalid_blast_id(self, token_first, campaign_in_db):
        """
        Try to get send of a blast but campaign id is invalid, we are expecting 404
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :return:
        """
        invalid_blast_id = sys.maxint
        campaign_id = campaign_in_db['id']
        get_blast_sends(invalid_blast_id, campaign_id, token_first, expected_status=(NOT_FOUND,))

    def test_get_campaign_blast_sends(self, token_first, campaign_in_db,
                                      campaign_blast):
        """
        Try to get sends with a valid campaign and blast id and we hope that we will get
        200 (OK) response.
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param campaign_blast: campaign blast object
        :return:
        """
        # 200 case: Got Campaign Sends successfully
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        response = get_blast_sends(blast_id, campaign_id, token_first, expected_status=(200,))
        # Since each blast have one send, so total sends will be equal to number of blasts
        assert response['count'] == 1
        assert len(response['sends']) == 1

    def test_get_campaign_blast_sends_with_user_from_same_domain(self, token_same_domain,
                                                                 campaign_in_db, campaign_blast):
        """
        Test if a user from same domain can access sends of a campaign blast or not.
        API should allow this user
        :param token_same_domain:
        :param campaign_in_db:
        :param campaign_blast:
        :return:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast_sends(blast_id, campaign_id, token_same_domain, expected_status=(200,))

    def test_get_campaign_blast_sends_with_user_from_diff_domain(self, token_second,
                                                                 campaign_in_db, campaign_blast):
        """
        Test if a user from same domain can not access sends of a campaign blast or not.
        API should not allow this user
        :param token_second:
        :param campaign_in_db:
        :param campaign_blast:
        :return:
        """
        blast_id = campaign_blast['id']
        campaign_id = campaign_in_db['id']
        get_blast_sends(blast_id, campaign_id, token_second, expected_status=(403,))
