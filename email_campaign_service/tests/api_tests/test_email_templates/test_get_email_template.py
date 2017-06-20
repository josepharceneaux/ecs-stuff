"""
    Test Email Template API: Contains tests for single Email Template.
"""
# Third Party
import requests

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.tests.modules.handy_functions import assert_valid_template_object
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  EMAIL_TEMPLATE_NOT_FOUND, EMAIL_TEMPLATE_FORBIDDEN)


class TestGETEmailTemplate(object):
    """
    Here are the tests of /v1/email-templates/:id
    """
    URL = EmailCampaignApiUrl.TEMPLATE
    HTTP_METHOD = 'get'

    def test_with_invalid_token(self):
        """
        Here we try to get email-template with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2,))

    def test_get_email_template_via_id(self, user_first, headers_same_for_email_templates, email_template):
        """
        Retrieve email_template via template's ID. We will create the email template using user_first
        and try to retrieve it using the template id returned in the response. user_same_domain with the same domain
        as the creator would be used to get the email template via id, verifying the users with same domain are
        allowed to access the templates created by fellow domain users. Response should be 200 (OK).
        """
        # Get email_template via template ID using token for 2nd user
        response = requests.get(url=self.URL % email_template['id'], headers=headers_same_for_email_templates)
        assert response.status_code == requests.codes.OK
        resp_dict = response.json()['template']
        assert_valid_template_object(resp_dict, user_first.id, [email_template['id']], email_template['name'])

    def test_with_non_existing_id(self, access_token_first_for_email_templates):
        """
        Retrieve email_template via ID for which email template doesn't exist.We will create the email
        template using user_first and try to retrieve it by appending some random value to the template id returned
        in the response. user_same_domain with the same domain as the creator would be used to get the email template
        via id, as users with same domain are allowed to access the templates created by fellow domain users.
        Response should be 400 (NOT FOUND) as template id we are using to get is non-existent.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(UserEmailTemplate, self.HTTP_METHOD, self.URL,
                                                               access_token_first_for_email_templates,
                                                               expected_error_code=EMAIL_TEMPLATE_NOT_FOUND[1])

    def test_get_email_template_with_user_of_other_domain(self, access_token_other):
        """
        Requesting an email-template with a user of some other domain. It should result in Forbidden error.
        """
        # Get email_template via template ID
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % fake.random_int(2, ),
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_get_with_user_of_other_valid_domain(self, email_template, access_token_other_for_email_templates):
        """
        Requesting an email-template with a user of some other domain. It should result in Forbidden error.
        """
        # Get email_template via template ID
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % email_template['id'],
                                                          access_token_other_for_email_templates,
                                                          expected_error_code=EMAIL_TEMPLATE_FORBIDDEN[1])
