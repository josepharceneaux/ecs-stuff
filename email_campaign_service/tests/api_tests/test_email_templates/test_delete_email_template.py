"""
    Test Email Template API: Contains tests for Email Template.
"""
# Third Party
import requests

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.custom_errors.campaign import (EMAIL_TEMPLATE_NOT_FOUND,
                                                                  EMAIL_TEMPLATE_FORBIDDEN,
                                                                  TEMPLATES_FEATURE_NOT_ALLOWED)
from email_campaign_service.tests.modules.handy_functions import request_to_email_template_resource


class TestDeleteEmailTemplate(object):
    """
    Here are the tests of /v1/email-templates/:id
    """
    URL = EmailCampaignApiUrl.TEMPLATE
    HTTP_METHOD = 'delete'

    def test_with_invalid_token(self):
        """
        Here we try to delete email-template with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, ))

    def test_with_non_existing_email_template(self, access_token_first_for_email_templates):
        """
        Test : To update email template by other user in the same domain
        Expect: 404 - NOT FOUND
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(UserEmailTemplate, self.HTTP_METHOD, self.URL,
                                                               access_token_first_for_email_templates,
                                                               expected_error_code=EMAIL_TEMPLATE_NOT_FOUND[1])

    def test_with_user_of_other_domain(self, access_token_other):
        """
        Requesting an email-template with a user of some other domain. It should result in Forbidden error.
        """
        # Get email_template via template ID
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % fake.random_int(2, ),
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_with_user_of_other_valid_domain(self, email_template, access_token_other_for_email_templates):
        """
        Requesting an email-template with a user of some other domain. It should result in Forbidden error.
        """
        # Get email_template via template ID
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % email_template['id'],
                                                          access_token_other_for_email_templates,
                                                          expected_error_code=EMAIL_TEMPLATE_FORBIDDEN[1])

    def test_delete_email_template(self, access_token_same_for_email_templates, email_template):
        """
        Tests deleting user's email template. Template should be deleted successfully returning
        204 (NO CONTENT) response.
        """
        resp = request_to_email_template_resource(access_token_same_for_email_templates, self.HTTP_METHOD,
                                                  email_template['id'])
        assert resp.status_code == requests.codes.NO_CONTENT
        template_after_delete = UserEmailTemplate.get_by_id(email_template['id'])
        assert template_after_delete is None
