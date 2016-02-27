"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/email-campaigns/:id/blasts/:id of
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
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignBlast)


class TestEmailCampaignBlastsWithId(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/blasts/:id
    """
    URL = EmailCampaignUrl.BLAST
    HTTP_METHOD = 'get'
    ENTITY = 'blast'

    def test_get_with_invalid_token(self, sent_campaign_with_client_id):
        """
         User auth token is invalid. It should result in Unauthorized error.
        :return:
        """
        blast_id = sent_campaign_with_client_id.blasts[0].id
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD,
            self.URL % (sent_campaign_with_client_id.id, blast_id),
            None)

    def test_get_with_valid_token(self, access_token_first, sent_campaign_with_client_id):
        """
        This is the test where we send a campaign and try to get its blast with valid
        access token. It should get OK response and number of sends should be 2.
        :return:
        """
        blast_id = sent_campaign_with_client_id.blasts[0].id
        response = requests.get(
            self.URL % (sent_campaign_with_client_id.id, blast_id),
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY,
                                                            check_count=False)
        json_resp = response.json()[self.ENTITY]
        assert json_resp['id'] == blast_id
        assert json_resp['campaign_id'] == sent_campaign_with_client_id.id
        assert json_resp['sends'] == 2

    def test_get_campaign_of_some_other_domain(self, access_token_first,
                                               email_campaign_in_other_domain):
        """
        This is the case where we try to get blast of a campaign which was created by
        user of some other domain. It should result in Forbidden error.
        :return:
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % (email_campaign_in_other_domain.id,
                                          fake.random_number()),
            access_token_first)

    def test_get_with_blast_id_associated_with_not_owned_campaign(
            self, access_token_first, access_token_other, campaign_with_valid_candidate,
            email_campaign_in_other_domain):
        """
        Here we assume that requested blast_id is associated with such a campaign which does not
        belong to domain of logged-in user. It should result in Forbidden error.
        """
        send_campaign(email_campaign_in_other_domain, access_token_other)
        blast_id = email_campaign_in_other_domain.blasts[0].id
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD,
            self.URL % (campaign_with_valid_candidate.id, blast_id),
            access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first,
                                          sent_campaign_with_client_id):
        """
        This is a test to get blasts of a campaign which does not exist in database.
        :return:
        """
        blast_id = sent_campaign_with_client_id.blasts[0].id
        CampaignsTestsHelpers.request_with_invalid_resource_id(
            EmailCampaign, self.HTTP_METHOD, self.URL % ('%s', blast_id),
            access_token_first,
            None)

    def test_get_with_invalid_blast_id(self, access_token_first,
                                       sent_campaign_with_client_id):
        """
        This is a test to get blasts of a campaign using non-existing blast_id
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(
            EmailCampaignBlast, self.HTTP_METHOD,
            self.URL % (sent_campaign_with_client_id.id, '%s'),
            access_token_first, None)
