"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/replies of
    SMS Campaign API.
"""
# Standard Imports
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import ResourceNotFound
from sms_campaign_service.common.campaign_services.common_tests import CampaignsCommonTests

# Service Specific
from sms_campaign_service.tests.modules.common_functions import assert_counts_and_replies_or_sends


class TestSmsCampaignReplies(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/replies
    """
    URL = SmsCampaignApiUrl.REPLIES
    METHOD = 'get'
    ENTITY = 'replies'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should get Unauthorized error.
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsCommonTests.request_with_invalid_token(self.METHOD, self.URL
                                                        % sms_campaign_of_current_user.id, None)

    def test_get_with_no_replies_on_campaign(self, auth_token, sms_campaign_of_current_user):
        """
        Here we are assuming that SMS campaign has been sent to candidates.
        And we didn't receive any reply from candidate. Replies count should be 0.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.REPLIES % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert_counts_and_replies_or_sends(response, entity=self.ENTITY)

    def test_get_with_deleted_campaign_id(self, auth_token, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its replies.
        It should get ResourceNotFound error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_get = requests.get(self.URL % sms_campaign_of_current_user.id,
                                    headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_get.status_code == ResourceNotFound.http_status_code(), \
            'Campaign should not be found (404)'

    def test_get_with_valid_token_and_one_reply(self, auth_token, candidate_phone_1,
                                                sms_campaign_of_current_user,
                                                create_campaign_replies):
        """
        This is the case where we assume we have received the replies on a campaign from 2
        candidates. We are using fixtures to create campaign blast and campaign replies.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_campaign_replies" to create an entry in database table "sms_campaign_replies",
        and then gets the "sends" of that campaign. Replies count should be 2.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert_counts_and_replies_or_sends(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['blast_id'] == sms_campaign_of_current_user.blasts[0].id
        assert json_resp['candidate_phone_id'] == candidate_phone_1.id

    def test_get_with_not_owned_campaign(self, auth_token, sms_campaign_of_other_user):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should get Forbidden error.
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(self.METHOD,
                                                         self.URL % sms_campaign_of_other_user.id,
                                                         auth_token)
