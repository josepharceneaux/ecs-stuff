"""
    Test Email Template API: Contains tests for Email Template Folders endpoints
"""
# Standard Library
import json

# Third Party
import pytest
import requests
from requests import codes

# Application Specific
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import (assert_and_delete_template_folder,
                                                                  create_template_folder)
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
        for folder_name in CampaignsTestsHelpers.INVALID_STRING:
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


class TestEmailTemplateFolder(object):
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
