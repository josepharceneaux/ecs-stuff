"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

     - GET /v1/email-campaigns/:id
"""
# Application Specific
from email_campaign_service.tests.conftest import EmailCampaign, fake
from email_campaign_service.common.routes import (EmailCampaignApiUrl)
from email_campaign_service.common.custom_errors.campaign import (EMAIL_CAMPAIGN_FORBIDDEN,
                                                                  EMAIL_CAMPAIGN_NOT_FOUND)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import (assert_valid_campaign_get,
                                                                  get_campaign_or_campaigns,
                                                                  assert_talent_pipeline_response)


class TestGetCampaign(object):
    """
    Here are the tests of GET /v1/email-campaigns/:id
    """
    URL = EmailCampaignApiUrl.CAMPAIGN
    HTTP_METHOD = 'get'

    def test_get_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, 100))

    def test_get_by_valid_campaign_id(self, email_campaign_user1_domain1_in_db, access_token_first, talent_pipeline):
        """
        This is the test to GET the campaign by providing campaign_id. It should get OK response
        """
        email_campaign = get_campaign_or_campaigns(access_token_first,
                                                   campaign_id=email_campaign_user1_domain1_in_db.id)
        assert_valid_campaign_get(email_campaign, [email_campaign_user1_domain1_in_db])

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first)

    def test_get_campaign_of_other_domain(self, email_campaign_user1_domain1_in_db, access_token_other):
        """
        Here we try to GET a campaign which is in some other domain. It should result-in
         ForbiddenError.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % email_campaign_user1_domain1_in_db.id,
            access_token_other, expected_error_code=EMAIL_CAMPAIGN_FORBIDDEN[1])

    def test_get_with_non_existing_campaign_id(self, access_token_first):
        """
        This is a test to get the blasts of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign, self.HTTP_METHOD,
                                                               self.URL, access_token_first,
                                                               expected_error_code=EMAIL_CAMPAIGN_NOT_FOUND[1])

    def test_get_by_campaign_id_with_fields(self, email_campaign_user1_domain1_in_db, access_token_first,
                                            talent_pipeline):
        """
        This is the test to GET the campaign by providing campaign_id & filters. It should get OK response
        """
        fields = ['id', 'subject', 'body_html', 'body_text', 'is_hidden']

        email_campaign = get_campaign_or_campaigns(access_token_first,
                                                   campaign_id=email_campaign_user1_domain1_in_db.id,
                                                   fields=fields)
        assert_valid_campaign_get(email_campaign, [email_campaign_user1_domain1_in_db], fields=fields)

        # Test GET api of talent-pipelines/:id/campaigns
        assert_talent_pipeline_response(talent_pipeline, access_token_first, fields=fields)

    def test_get_campaign_with_email_client(self, email_campaign_with_outgoing_email_client, access_token_first):
        """
        Here we try to GET a campaign which is created by email-client. It should not get any error.
        """
        campaign = email_campaign_with_outgoing_email_client
        fields = ['email_client_credentials_id']
        email_campaign = get_campaign_or_campaigns(access_token_first, campaign_id=campaign['id'], fields=fields)
        assert_valid_campaign_get(email_campaign, [campaign], fields=fields)
