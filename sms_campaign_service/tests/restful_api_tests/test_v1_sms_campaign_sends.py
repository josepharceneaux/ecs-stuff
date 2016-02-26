"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/sends of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.error_handling import UnauthorizedError
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestSmsCampaignSends(object):
    """
    This class contains tests for endpoint /campaigns/:id/sends
    """
    URL = SmsCampaignApiUrl.SENDS
    METHOD = 'get'
    ENTITY = 'sends'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should result in Unauthorized error.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should not be authorized (401)'

    def test_get_with_no_campaign_sent(self, access_token_first, sms_campaign_of_current_user):
        """
        Here we are assuming that SMS campaign has not been sent to any of candidates,
        So no blast should be saved for the campaign. Sends count should be 0.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response)

    def test_get_with_no_candidate_associated_to_campaign(self, access_token_first,
                                                          sms_campaign_of_current_user,
                                                          create_sms_campaign_blast):
        """
        Here we are assuming that SMS campaign has been sent but no candidate was associated with
        the associated smartlists. So, sends count should be 0.

        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_blast" to create an entry in database table "sms_campaign_blast",
        and then gets the "sends" of that campaign.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :param create_sms_campaign_blast: fixture to create entry in "sms_campaign_blast" db table.
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response)

    def test_get_with_deleted_campaign(self, access_token_first, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its sends.
        It should result in ResourceNotFound error.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                             SmsCampaignApiUrl.CAMPAIGN,
                                                             self.URL, self.METHOD,
                                                             access_token_first)

    def test_get_with_valid_token_and_two_sends(self, access_token_first, candidate_first,
                                                sms_campaign_of_current_user,
                                                create_campaign_sends):
        """
        This is the case where we assume we have sent the campaign to 2 candidates. We are
        using fixtures to create campaign blast and campaign sends.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_sends" to create an entry in database table "sms_campaign_sends",
        and then gets the "sends" of that campaign. Sends count should be 2.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['blast_id'] == sms_campaign_of_current_user.blasts[0].id
        assert json_resp['candidate_id'] == candidate_first.id

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in Forbidden error.
        :return:
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.METHOD,
                                                         self.URL % sms_campaign_in_other_domain.id,
                                                         access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get campaign sends of a campaign which does not exist in database.
        :param access_token_first:
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_campaign_id(SmsCampaign,
                                                              self.METHOD,
                                                              self.URL,
                                                              access_token_first,
                                                              None)
