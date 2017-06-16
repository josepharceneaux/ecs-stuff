"""
    Test Email Template API: Contains tests for Email Template Folders endpoints
"""
# Third Party
import requests

# Application Specific
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.custom_errors.campaign import TEMPLATES_FEATURE_NOT_ALLOWED
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import assert_and_delete_template_folder


class TestDeleteTemplateFolder(object):
    """
    This contains tests for deleting an email-template folder
    """

    def test_delete_email_template_folder(self, headers_for_email_templates, create_email_template_folder):
        """
        Test for deleting email template folder with user who created the folder.
        It creates a test folder by user_first and deletes that by the user_same_domain of same domain.
        This verifies that the users of the same domain having appropriate privileges are able to delete
        email template folders created by users of same domain. Deletion should be successful and
        a response of 204 (NO_CONTENT) must be returned.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = create_email_template_folder
        assert_and_delete_template_folder(template_folder_id, headers_for_email_templates)

    def test_delete_email_template_folder_with_user_of_same_domain(self, create_email_template_folder,
                                                                   headers_same_for_email_templates):
        """
        Test for deleting email template folder with another user of same domain.
        It creates a test folder by user_first and deletes that by the user_same_domain of same domain.
        This verifies that the users of the same domain having appropriate privileges are able to delete
        email template folders created by users of same domain. Deletion should be successful and
        a response of 204 (NO_CONTENT) must be returned.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = create_email_template_folder
        assert_and_delete_template_folder(template_folder_id, headers_same_for_email_templates)

    def test_delete_email_template_folder_with_user_of_other_domain(self, create_email_template_folder,
                                                                    access_token_other):
        """
        Test for deleting email template folder with user of some other domain.
        It should result in Forbidden error.
        """
        # Get Template Folder Id
        template_folder_id, _ = create_email_template_folder
        CampaignsTestsHelpers.request_for_forbidden_error('delete',
                                                          EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])


class TestEmailTemplatesInFolders(object):
    """
    Here are the tests of /v1/email-template-folders/:id/email-templates
    """
    URL = EmailCampaignApiUrl.TEMPLATES_IN_FOLDER

    def test_get_templates_in_a_folder(self, create_email_template_folder, headers_for_email_templates,
                                       headers_same_for_email_templates, headers_other):
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
        response = requests.get(url=self.URL % template_folder_id, headers=headers_other)
        assert response.status_code == requests.codes.FORBIDDEN, response.text

    def test_get_saved_templates_in_a_folder(self, create_email_template_folder, headers_for_email_templates,
                                             headers_same_for_email_templates,
                                             headers_other, email_templates_bulk):
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
        response = requests.get(url=self.URL % template_folder_id, headers=headers_other)
        assert response.status_code == requests.codes.FORBIDDEN, response.text
