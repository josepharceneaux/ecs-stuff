"""
    Test Email Template API: Contains tests for Email Template Folders endpoint:

    - /v1/email-template-folders/:id/email-templates
"""

# Third Party
import requests

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  TEMPLATE_FOLDER_FORBIDDEN,
                                                                  TEMPLATE_FOLDER_NOT_FOUND)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestGetEmailTemplatesInFolders(object):
    """
    Here are the tests of /v1/email-template-folders/:id/email-templates
    """
    HTTP_METHOD = 'get'
    URL = EmailCampaignApiUrl.TEMPLATES_IN_FOLDER

    def test_with_invalid_token(self):
        """
        Here we try to delete email-template-folder with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, ))

    def test_get_templates_in_a_folder(self, create_email_template_folder, headers_for_email_templates,
                                       headers_same_for_email_templates, access_token_other):
        """
        Test for getting email-templates associated with a template folder.
        We have not created any email-templates, so there should not exist any email-template in template-folder
        """
        template_folder_id, _ = create_email_template_folder
        for auth_header in (headers_for_email_templates, headers_same_for_email_templates):
            response = requests.get(url=self.URL % template_folder_id, headers=auth_header)
            assert response.status_code == requests.codes.OK, response.text
            email_templates = response.json()['email_templates']
            assert len(email_templates) == 0

        # Request with user of some other domain
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % template_folder_id,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_get_saved_templates_in_a_folder(self, create_email_template_folder, headers_for_email_templates,
                                             headers_same_for_email_templates,
                                             access_token_other, email_templates_bulk):
        """
        Test for getting saved email-templates associated with a template folder.
        Here we are using fixture "email_templates_bulk" to create 10 email-templates in template folder.
        """
        template_folder_id, _ = create_email_template_folder
        for auth_header in (headers_for_email_templates, headers_same_for_email_templates):
            response = requests.get(url=self.URL % template_folder_id, headers=auth_header)
            assert response.status_code == requests.codes.OK, response.text
            email_templates = response.json()['email_templates']
            assert len(email_templates) == 10

        # Request with user of some other domain
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % template_folder_id,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_get_with_user_of_other_valid_domain(self, create_email_template_folder,
                                                 access_token_other_for_email_templates):
        """
        Test for deleting email template folder with user of some other domain.
        It should result in Forbidden error.
        """
        # Get Template Folder Id
        template_folder_id, _ = create_email_template_folder
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % template_folder_id,
                                                          access_token_other_for_email_templates,
                                                          expected_error_code=TEMPLATE_FOLDER_FORBIDDEN[1])

    def test_get_with_invalid_folder_id(self, access_token_first_for_email_templates):
        """
        Test with non-existing email template folder. It should result in Resource not found error.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailTemplateFolder, self.HTTP_METHOD, self.URL,
                                                               access_token_first_for_email_templates,
                                                               expected_error_code=TEMPLATE_FOLDER_NOT_FOUND[1]
                                                               )
