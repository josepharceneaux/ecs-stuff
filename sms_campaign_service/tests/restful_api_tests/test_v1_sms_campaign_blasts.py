"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/blasts of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.campaign_services.common_tests import CampaignsCommonTests

# Service Specific
from sms_campaign_service.tests.modules.common_functions import assert_ok_response_and_counts


class TestSmsCampaignBlasts(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/blasts
    """
    URL = SmsCampaignApiUrl.BLASTS
    METHOD = 'get'
    ENTITY = 'blasts'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should get Unauthorized error.
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsCommonTests.request_with_invalid_token(self.METHOD, self.URL
                                                        % sms_campaign_of_current_user.id, None)

    def test_get_with_no_blasts_saved(self, auth_token, sms_campaign_of_current_user):
        """
        Here we assume that there is no blast saved for given campaign. We should get OK
        response and count should be 0.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_with_deleted_campaign(self, auth_token, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its blasts.
        It should get ResourceNotFound error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsCommonTests.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                             SmsCampaignApiUrl.CAMPAIGN,
                                                             self.URL, self.METHOD, auth_token)

    def test_get_with_saved_blasts(self, auth_token, candidate_phone_1,
                                   sms_campaign_of_current_user,
                                   create_campaign_replies, create_campaign_sends):
        """
        This is the case where we assume we have blast saved with one reply and 2 sends.
        We are using fixtures to create campaign blast and campaign replies and sends.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_campaign_replies" to create an entry in database table "sms_campaign_replies",
        and then gets the "sends" of that campaign. Replies count should be 1 and sends count
        should be 2.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['id'] == sms_campaign_of_current_user.blasts[0].id
        assert json_resp['campaign_id'] == sms_campaign_of_current_user.id
        assert json_resp['sends'] == 2
        assert json_resp['replies'] == 1

    def test_get_with_not_owned_campaign(self, auth_token, sms_campaign_of_other_user):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should get Forbidden error.
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(self.METHOD,
                                                         self.URL % sms_campaign_of_other_user.id,
                                                         auth_token)
