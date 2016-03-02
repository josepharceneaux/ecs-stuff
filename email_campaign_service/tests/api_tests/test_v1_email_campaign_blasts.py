"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/email-campaigns/:id/blasts of
    email campaign API.
"""
# Standard Imports
import time

# Third Party
import requests

# Common Utils
from email_campaign_service.common.models.db import db
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestEmailCampaignBlasts(object):
    """
    This class contains tests for endpoint /v1/email-campaigns/:id/blasts
    """
    # URL of this endpoint
    URL = EmailCampaignUrl.BLASTS
    # HTTP Method for this endpoint
    HTTP_METHOD = 'get'
    # Resource for this endpoint
    ENTITY = 'blasts'

    def test_get_with_invalid_token(self, campaign_with_valid_candidate):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL
                                                         % campaign_with_valid_candidate.id, None)

    def test_get_with_no_campaign_sent(self, access_token_first, campaign_with_valid_candidate):
        """
        Here we assume that there is no blast saved for given campaign. We should get OK
        response and count should be 0.
        """
        response = requests.get(self.URL % campaign_with_valid_candidate.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_by_sending_campaign(self, access_token_first, sent_campaign):
        """
        Here we first send the campaign to 2 candidates (with and without email-client-id).
        We then assert that blast has been created by making HTTP
        GET call on endpoint /v1/email-campaigns/:id/blasts
        """
        response = requests.get(self.URL % sent_campaign.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        db.session.commit()
        assert json_resp['id'] == sent_campaign.blasts[0].id
        assert json_resp['campaign_id'] == sent_campaign.id
        assert json_resp['sends'] == 2

    def test_get_not_owned_campaign(self, access_token_first, email_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in 'forbidden' error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % email_campaign_in_other_domain.id, access_token_first)

    def test_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get the blasts of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)
