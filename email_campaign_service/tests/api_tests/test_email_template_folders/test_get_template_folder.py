"""
    Test Email Template API: Contains tests for getting single Email Template Folder.
"""
# Third Party
import requests

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  TEMPLATE_FOLDER_NOT_FOUND,
                                                                  TEMPLATE_FOLDER_FORBIDDEN)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestGetEmailTemplateFolder(object):
    """
    This contains tests for accessing single template folder
    """

    HTTP_METHOD = 'get'
    URL = EmailCampaignApiUrl.TEMPLATE_FOLDER
    ENTITY = 'email_template_folder'

    def test_with_invalid_token(self):
        """
        Here we try to get email-template-folder with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, ))

    def test_get_email_template_folder_with_user_of_other_domain(self, create_email_template_folder,
                                                                 access_token_other):
        """
        Test for retrieving email template folder with user of some other domain.
        It should result in Forbidden error.
        """
        # Get Template Folder Id
        template_folder_id, _ = create_email_template_folder
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % template_folder_id,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_get_with_invalid_folder_id(self, access_token_first_for_email_templates):
        """
        Test for retrieving non-existing email template folder.
        It should result in Resource not found error.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailTemplateFolder, self.HTTP_METHOD, self.URL,
                                                               access_token_first_for_email_templates,
                                                               expected_error_code=TEMPLATE_FOLDER_NOT_FOUND[1]
                                                               )

    def test_get_folder_of_some_other_valid_domain(self, create_email_template_folder,
                                                   access_token_other_for_email_templates):
        """
        Test for retrieving email template folder with user of some other domain.
        It should result in Forbidden error.
        """
        folder_id, _ = create_email_template_folder
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % folder_id,
                                                          access_token_other_for_email_templates,
                                                          expected_error_code=TEMPLATE_FOLDER_FORBIDDEN[1]
                                                          )

    def test_get_valid_email_template_folder(self, create_email_template_folder, headers_for_email_templates):
        """
        Test for retrieving valid email template folder. It should not result in any error.
        """
        folder_id, folder_name = create_email_template_folder
        response = requests.get(self.URL % folder_id, headers=headers_for_email_templates)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY, check_count=False)
        json_resp = response.json()[self.ENTITY]
        assert json_resp['id'] == folder_id
        assert json_resp['name'] == folder_name
