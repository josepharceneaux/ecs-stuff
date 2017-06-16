"""
    Test Email Template API: Contains tests for Email Template Folders endpoints
"""

# Third Party
import requests

# Application Specific
from email_campaign_service.common.routes import EmailCampaignApiUrl


class TestGetEmailTemplatesInFolders(object):
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
