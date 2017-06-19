"""
    Test Email Template API: Contains tests for deleting single Email Template Folder.
"""

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  TEMPLATE_FOLDER_FORBIDDEN,
                                                                  TEMPLATE_FOLDER_NOT_FOUND)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import assert_and_delete_template_folder


class TestDeleteTemplateFolder(object):
    """
    This contains tests for deleting an email-template folder
    """
    HTTP_METHOD = 'delete'
    URL = EmailCampaignApiUrl.TEMPLATE_FOLDER

    def test_with_invalid_token(self):
        """
        Here we try to delete email-template-folder with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, ))

    def test_delete_email_template_folder(self, headers_for_email_templates, email_template_folder):
        """
        Test for deleting email template folder with user who created the folder.
        It creates a test folder by user_first and deletes that by the user_same_domain of same domain.
        This verifies that the users of the same domain having appropriate privileges are able to delete
        email template folders created by users of same domain. Deletion should be successful and
        a response of 204 (NO_CONTENT) must be returned.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = email_template_folder
        assert_and_delete_template_folder(template_folder_id, headers_for_email_templates)

    def test_delete_email_template_folder_with_user_of_same_domain(self, email_template_folder,
                                                                   headers_same_for_email_templates):
        """
        Test for deleting email template folder with another user of same domain.
        It creates a test folder by user_first and deletes that by the user_same_domain of same domain.
        This verifies that the users of the same domain having appropriate privileges are able to delete
        email template folders created by users of same domain. Deletion should be successful and
        a response of 204 (NO_CONTENT) must be returned.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = email_template_folder
        assert_and_delete_template_folder(template_folder_id, headers_same_for_email_templates)

    def test_delete_email_template_folder_with_user_of_other_domain(self, email_template_folder,
                                                                    access_token_other):
        """
        Test for deleting email template folder with user of some other domain.
        It should result in Forbidden error.
        """
        # Get Template Folder Id
        template_folder_id, _ = email_template_folder
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % template_folder_id,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_delete_email_template_folder_with_user_of_other_valid_domain(self, email_template_folder,
                                                                          access_token_other_for_email_templates):
        """
        Test for deleting email template folder with user of some other domain.
        It should result in Forbidden error.
        """
        # Get Template Folder Id
        template_folder_id, _ = email_template_folder
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % template_folder_id,
                                                          access_token_other_for_email_templates,
                                                          expected_error_code=TEMPLATE_FOLDER_FORBIDDEN[1])

    def test_delete_with_invalid_folder_id(self, access_token_first_for_email_templates):
        """
        Test for deleting non-existing email template folder. It should result in Resource not found error.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailTemplateFolder, self.HTTP_METHOD, self.URL,
                                                               access_token_first_for_email_templates,
                                                               expected_error_code=TEMPLATE_FOLDER_NOT_FOUND[1]
                                                               )
