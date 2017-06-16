"""
    Test Email Template API: Contains tests for Email Template Folders endpoints
"""
# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.custom_errors.campaign import TEMPLATES_FEATURE_NOT_ALLOWED
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestGetEmailTemplateFolder(object):
    """
    This contains tests for accessing single template folder
    """

    HTTP_METHOD = 'get'
    URL = EmailCampaignApiUrl.TEMPLATE_FOLDER

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
