"""
    Test Email Template API: Contains tests for Email Template.
"""
# Standard Library
import datetime

# Third Party
import requests

# Application Specific
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.custom_errors.campaign import EMAIL_TEMPLATE_NOT_FOUND, \
    TEMPLATES_FEATURE_NOT_ALLOWED, EMAIL_TEMPLATE_FORBIDDEN, INVALID_REQUEST_BODY
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.tests.modules.handy_functions import (request_to_email_template_resource,
                                                                  update_email_template, assert_valid_template_object)


class TestUPDATEEmailTemplate(object):
    """
    Here are the tests of /v1/email-templates/:id
    """
    URL = EmailCampaignApiUrl.TEMPLATE
    HTTP_METHOD = 'patch'

    def test_with_invalid_token(self):
        """
        Here we try to create email-template-folder with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, ))

    def test_update_with_invalid_data(self, email_template, headers_for_email_templates,
                                      access_token_first_for_email_templates):
        """
        Trying to create email template with 1) no data and 2) Non-JSON data. It should result in invalid usage error.
        """
        for data in (email_template, None):
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL % email_template['id'],
                                                             access_token_first_for_email_templates,
                                                             data=data, is_json=False,
                                                             expected_error_code=INVALID_REQUEST_BODY[1])

    def test_update_email_template(self, user_first, email_template, user_same_domain,
                                   access_token_same_for_email_templates):
        """
        To update email template by other user in the same domain
        Response should be 200 (OK)
        """
        updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                                '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail' \
                                ' testing through script</p>\r\n</body>\r\n</html>\r\n'

        # Get email_template via template ID
        resp = update_email_template(email_template['id'], 'patch', access_token_same_for_email_templates,
                                     user_same_domain.id,
                                     email_template['name'],
                                     updated_template_body, email_template['template_folder_id'],
                                     email_template['domain_id'])
        assert resp.status_code == requests.codes.OK, resp.text
        resp_dict = resp.json()['template']
        assert_valid_template_object(resp_dict, user_first.id, [email_template['id']], email_template['name'],
                                     updated_template_body)

    def test_update_non_existing_email_template(self, access_token_first_for_email_templates):
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
