"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/sends of email-campaign API.
"""
# Third Party
import requests

# Common Utils
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestEmailCampaignSends(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/sends/:id/sends
    """
    URL = EmailCampaignUrl.SENDS
    HTTP_METHOD = 'get'
    ENTITY = 'sends'

    def test_get_with_invalid_token(self, campaign_with_valid_candidate):
        """
         User auth token is invalid. It should result in Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD, self.URL % campaign_with_valid_candidate.id, None)

    def test_get_with_no_campaign_sent(self, access_token_first, campaign_with_valid_candidate):
        """
        Here we are assuming that email campaign has not been sent to any candidate. Sends count
        should be 0.
        """
        response = requests.get(
            self.URL % campaign_with_valid_candidate.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_by_sending_campaign(self, access_token_first, sent_campaign_with_client_id):
        """
        Here we first send the campaign to 2 candidates (using email_client_id so that campaign
        is not actually sent). We then assert that sends has been created by making HTTP
        GET call on endpoint /v1/email-campaigns/:id/sends
        """
        # send campaign
        response = requests.get(self.URL % sent_campaign_with_client_id.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['campaign_id'] == sent_campaign_with_client_id.id
        assert json_resp['candidate_id'] == sent_campaign_with_client_id.sends[0].candidate_id

    def test_get_not_owned_campaign(self, access_token_first, email_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in 'forbidden' error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % email_campaign_in_other_domain.id, access_token_first)

    def test_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get the sends of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)
