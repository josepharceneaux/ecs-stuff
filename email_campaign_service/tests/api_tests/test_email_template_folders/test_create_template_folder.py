"""
    Test Email Template API: Contains tests for creating Email Template Folder.
"""
# Third Party
import pytest
import requests

# Application Specific
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.tests.modules.handy_functions import  create_template_folder
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  INVALID_REQUEST_BODY, INVALID_INPUT,
                                                                  NOT_NON_ZERO_NUMBER, DUPLICATE_TEMPLATE_FOLDER_NAME,
                                                                  TEMPLATE_FOLDER_NOT_FOUND, TEMPLATE_FOLDER_FORBIDDEN)


def test_s3_url_for_domain_ids_for_email_templates():
    """
    This test is to  certify that email template folder can't be created by using
    parent_id which doesn't exist. Should return 400 bad request.
    """
    url = app.config[TalentConfigKeys.URL_FOR_DOMAINS_FOR_EMAIL_TEMPLATES]
    response = requests.get(url)
    assert response.ok, response.text


class TestCreateEmailTemplateFolders(object):
    """
    Here are the tests of /v1/email-template-folders
    """
    HTTP_METHOD = 'post'
    URL = EmailCampaignApiUrl.TEMPLATE_FOLDERS

    def test_with_invalid_token(self):
        """
        Here we try to create email-template-folder with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_with_invalid_data(self, access_token_first_for_email_templates):
        """
        Trying to create a template folder with 1) no data and 2) Non-JSON data.
        It should result in invalid usage error.
        """
        template_folder_name = 'test_template_folder_{}'.format(fake.uuid4())
        data = {'name': template_folder_name}
        for data in (data, None):
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                             access_token_first_for_email_templates,
                                                             data=data, is_json=False,
                                                             expected_error_code=INVALID_REQUEST_BODY[1])

    def test_create_email_template_folder_with_valid_data(self, headers_for_email_templates):
        """
        Test for creating new email template folder. This should not get any error.
        """
        template_folder_id, template_folder_name = create_template_folder(headers_for_email_templates)
        assert template_folder_id and template_folder_id > 0, 'Expecting positive folder_id'
        assert template_folder_name, 'Expecting non-empty string of folder_name'

    @pytest.mark.qa
    def test_create_email_template_folder_with_same_name(self, create_email_template_folder,
                                                         access_token_first_for_email_templates):
        """
        This test makes sure that email template folder is not created with same
        name which already exist. It should return 400 bad request.
        """
        template_folder_id, template_folder_name = create_email_template_folder
        data = {'name': template_folder_name, 'is_immutable': 1}
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                         access_token_first_for_email_templates,
                                                         data, expected_error_code=DUPLICATE_TEMPLATE_FOLDER_NAME[1])

    def test_create_email_template_folder_with_invalid_data_types(self, access_token_first_for_email_templates):
        """
        This test is to certify that create email template folder with invalid data_types isn't possible.
        It should result in 400 bad request.
        """
        for folder_name in CampaignsTestsHelpers.INVALID_STRINGS:
            data = {'name': folder_name}
            print "Iterating key:{}, value:{}".format('name', folder_name)
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                             access_token_first_for_email_templates, data,
                                                             expected_error_code=INVALID_INPUT[1])

        data = {'name': fake.word()}
        for key in ('parent_id', 'is_immutable'):
            for invalid_value in CampaignsTestsHelpers.INVALID_STRINGS:
                data[key] = invalid_value
                print "Iterating key:{}, value:{}".format(key, invalid_value)
                CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                                 access_token_first_for_email_templates, data,
                                                                 expected_error_code=NOT_NON_ZERO_NUMBER[1])

    @pytest.mark.qa
    def test_create_email_template_folder_with_non_existing_parent_id(self, access_token_first_for_email_templates):
        """
        This test is to  certify that email template folder can't be created by using
        parent_id which doesn't exist. It should result in 400 bad request.
        """
        non_existing_parent_id = CampaignsTestsHelpers.get_non_existing_id(EmailTemplateFolder)
        data = {'name': fake.word(), 'parent_id': non_existing_parent_id}
        CampaignsTestsHelpers.request_for_resource_not_found_error(self.HTTP_METHOD, self.URL,
                                                                   access_token_first_for_email_templates, data,
                                                                   expected_error_code=TEMPLATE_FOLDER_NOT_FOUND[1])

    @pytest.mark.qa
    def test_create_email_template_folder_with_parent_id_of_other_domain(self, create_email_template_folder,
                                                                         access_token_other_for_email_templates):
        """
        This test is to assure that email template folder can't be created through
        parent_id of the other domain folder. It should result in 403.
        """
        template_folder_id, template_folder_name = create_email_template_folder
        data = {'name': fake.sentence(), 'is_immutable': 1, 'parent_id': template_folder_id}
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL,
                                                          access_token_other_for_email_templates, data,
                                                          expected_error_code=TEMPLATE_FOLDER_FORBIDDEN[1])

    def test_create_email_template_folder_with_invalid_domain(self, access_token_other):
        """
        This test is to assure that email template folder can't be created through the user of domain other
        than Kaiser's. Should result in Forbidden error.
        """
        data = {'name': fake.sentence()}
        CampaignsTestsHelpers.request_for_forbidden_error('post', EmailCampaignApiUrl.TEMPLATE_FOLDERS,
                                                          access_token_other, data,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])
