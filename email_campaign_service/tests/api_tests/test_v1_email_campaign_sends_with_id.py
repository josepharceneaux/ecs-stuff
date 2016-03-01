"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/email-campaigns/:id/sends/:id of
    Email Campaign API.
"""
# Third Party
import requests

# Service Specific
from email_campaign_service.tests.modules.handy_functions import send_campaign

# Common Utils
from email_campaign_service.common.tests.sample_data import fake
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignSend)


class TestEmailCampaignSendsWithId(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/sends/:id
    """
    URL = EmailCampaignUrl.SEND_BY_ID
    HTTP_METHOD = 'get'
    ENTITY = 'send'

    def test_get_with_invalid_token(self, sent_campaign_with_client_id):
        """
         User auth token is invalid. It should result in Unauthorized error.
        """
        for send in sent_campaign_with_client_id.sends:
            CampaignsTestsHelpers.request_with_invalid_token(
                self.HTTP_METHOD,
                self.URL % (sent_campaign_with_client_id.id, send.id),
                None)

    def test_get_with_valid_token(self, access_token_first, sent_campaign_with_client_id):
        """
        Here we user `sent_campaign_with_client_id` fixture to send campaign via email-client-id
        to 2 candidates. This is the test where we get campaign's sends with valid
        access token.
        """
        for send in sent_campaign_with_client_id.sends:
            response = requests.get(
                self.URL % (sent_campaign_with_client_id.id, send.id),
                headers=dict(Authorization='Bearer %s' % access_token_first))
            CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY,
                                                                check_count=False)
            json_resp = response.json()[self.ENTITY]
            assert json_resp['id'] == send.id
            assert json_resp['campaign_id'] == sent_campaign_with_client_id.id
            assert json_resp['candidate_id'] == send.candidate_id

    def test_get_campaign_of_some_other_domain(self, access_token_first,
                                               email_campaign_in_other_domain):
        """
        This is the case where we try to get send object of such a campaign which was created by
        user of some other domain. It should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % (email_campaign_in_other_domain.id,
                                          fake.random_number()),
            access_token_first)

    def test_get_with_send_id_associated_with_not_owned_campaign(
            self, access_token_first, access_token_other, campaign_with_valid_candidate,
            email_campaign_in_other_domain):
        """
        Here we assume that requested send is associated with such a campaign which does not
        belong to domain of logged-in user. It should result in Forbidden error.
        """
        send_campaign(email_campaign_in_other_domain, access_token_other)
        for send in email_campaign_in_other_domain.sends:
            CampaignsTestsHelpers.request_for_forbidden_error(
                self.HTTP_METHOD,
                self.URL % (campaign_with_valid_candidate.id, send.id),
                access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first,
                                          sent_campaign_with_client_id):
        """
        This is a test to get send object of a campaign which does not exist in database.
        """
        for send in sent_campaign_with_client_id.sends:
            CampaignsTestsHelpers.request_with_invalid_resource_id(
                EmailCampaign, self.HTTP_METHOD, self.URL % ('%s', send.id),
                access_token_first,
                None)

    def test_get_with_invalid_send_id(self, access_token_first,
                                      sent_campaign_with_client_id):
        """
        This is a test to get send object of a campaign using non-existing send_id
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(
            EmailCampaignSend, self.HTTP_METHOD,
            self.URL % (sent_campaign_with_client_id.id, '%s'),
            access_token_first, None)
