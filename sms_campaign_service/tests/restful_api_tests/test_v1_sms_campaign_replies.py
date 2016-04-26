"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/replies of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestSmsCampaignReplies(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns/:id/replies
    """
    URL = SmsCampaignApiUrl.REPLIES
    HTTP_METHOD = 'get'
    ENTITY = 'replies'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should result in Unauthorized error.
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL
                                                         % sms_campaign_of_current_user['id'], None)

    def test_get_with_no_replies_on_campaign(self, access_token_first,
                                             sms_campaign_of_current_user):
        """
        Here we are assuming that SMS campaign has been sent to candidates.
        And we didn't receive any reply from candidate. Replies count should be 0.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        """
        response = requests.get(self.URL % sms_campaign_of_current_user['id'],
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_with_deleted_campaign(self, access_token_first, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its replies.
        It should result in ResourceNotFound error.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                              SmsCampaignApiUrl.CAMPAIGN,
                                                              self.URL, self.HTTP_METHOD,
                                                              access_token_first)

    def test_get_with_valid_token_and_one_reply(self, access_token_first, candidate_and_phone_1,
                                                sent_campaign_and_blast_ids,
                                                create_campaign_replies):
        """
        This is the case where we assume we have received the replies on a campaign from 1
        candidate. We are using fixtures to create campaign blast and campaign replies.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_campaign_replies" to create an entry in database table "sms_campaign_replies".
        Replies count should be 1.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        response = requests.get(self.URL % campaign['id'],
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['blast_id'] == blast_ids[0]
        assert json_resp['candidate_phone_id'] == candidate_and_phone_1[1]['id']

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain):
        """
        This is the case where we try to get replies of a campaign which was created by
        some other user. It should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % sms_campaign_in_other_domain['id'],
                                                          access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get campaign replies of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)
