"""
    Test Email Template API: Contains tests for getting Email Template Folders.
"""
# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.custom_errors.campaign import TEMPLATES_FEATURE_NOT_ALLOWED
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestGetTemplateFolders(object):
    """
    This contains tests for getting template folders.
    """

    HTTP_METHOD = 'get'
    URL = EmailCampaignApiUrl.TEMPLATE_FOLDERS

    def test_with_invalid_token(self):
        """
        Here we try to get email template folders with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_get_email_template_folders_in_domain(self, headers_for_email_templates, email_template_folders_bulk,
                                                  headers_same_for_email_templates, headers_other_for_email_templates):
        """
        In this test, we get email template folders in a domain
        """
        # Get by one user and some other user of same domain
        for headers in (headers_for_email_templates, headers_same_for_email_templates):
            response = requests.get(url=self.URL, headers=headers)
            assert response.status_code == codes.OK, response.text
            json_response = response.json()
            assert 'template_folders' in json_response
            assert len(json_response['template_folders']) == 20

        # Get by user of some other domain
        response = requests.get(url=self.URL, headers=headers_other_for_email_templates)
        assert response.status_code == codes.OK, response.text
        json_response = response.json()
        assert 'template_folders' in json_response
        assert len(json_response['template_folders']) == 0

    def test_get_email_template_folders_with_invalid_domain(self, access_token_other):
        """
        This test is to assure that email template folder can't be get through the user of domain other
        than Kaiser's. Should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])
