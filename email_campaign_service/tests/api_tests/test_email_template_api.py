"""Test Email Template API: Contains tests for Email Templates and Email Template Folders endpoints
"""
# Standard Library
import json
import datetime
# Third Party
import requests
from requests import codes
import pytest
# Application Specific
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.tests.modules.handy_functions import (request_to_email_template_resource,
                                                                  EMAIL_TEMPLATE_BODY, update_email_template,
                                                                  add_email_template, assert_valid_template_object,
                                                                  data_to_create_email_template,
                                                                  post_to_email_template_resource,
                                                                  EMAIL_TEMPLATE_INVALID_DATA_TYPES,
                                                                  assert_and_delete_template_folder)


class TestEmailTemplateFolders(object):
    """
    Here are the tests of /v1/email-template-folders
    """

    def test_create_email_template_folder(self, create_email_template_folder):
        """
        Test for creating new email template folder
        It creates a test folder and asserts that it is created with correct name.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = create_email_template_folder
        assert template_folder_id
        assert template_folder_name

    @pytest.mark.qa
    def test_delete_email_template_folder(self, headers_same, create_email_template_folder):
        """
        Test for deleting email template folder.
        It creates a test folder by user_first and deletes that by the user_same_domain of same domain.
        This verifies that the users of the same domain having appropriate privileges are able to delete
        email template folders created by users of same domain. Deletion should be successful and
        a response of 204 (NO_CONTENT) must be returned.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = create_email_template_folder
        data = {'name': template_folder_name}
        assert_and_delete_template_folder(template_folder_id, headers_same, data=json.dumps(data))

    @pytest.mark.qa
    def test_create_email_template_folder_with_same_name(self, headers, create_email_template_folder):
        """
        This test makes sure that email template folder is not created with same
        name which already exist. Should return 400 bad request.
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = create_email_template_folder
        data = {'name': template_folder_name,
                'is_immutable': 1}
        response = requests.post(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, data=json.dumps(data),
                                 headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=requests.codes.BAD_REQUEST)

    @pytest.mark.qa
    def test_create_email_template_folder_with_invalid_data_type(self, headers):
        """
        This test is to certify that create email template with invalid data_types isn't possible.
        Should return 400 bad request.
        """
        for param in EMAIL_TEMPLATE_INVALID_DATA_TYPES:
            response = requests.post(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, data=json.dumps(param),
                                     headers=headers)
            CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=requests.codes.BAD_REQUEST)

    @pytest.mark.qa
    def test_create_email_template_folder_with_non_existing_parent_id(self, headers):
        """
        This test is to  certify that email template folder can't be created by using
        parent_id which doesn't exist. Should return 400 bad request.
        """
        non_existing_parent_id = CampaignsTestsHelpers.get_non_existing_id(EmailTemplateFolder)
        data = {'name': fake.word(), 'is_immutable': 1, 'parent_id': non_existing_parent_id}
        response = requests.post(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, data=json.dumps(data),
                                 headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=requests.codes.NOT_FOUND)

    @pytest.mark.qa
    def test_create_email_template_folder_with_deleted_parent_id(self, headers, create_email_template_folder):
        """
        This test is to assure that email template folder can't be created through
        parent_id of the folder which is deleted. Should return 400 bad request.
        """
        template_folder_id, template_folder_name = create_email_template_folder
        assert_and_delete_template_folder(template_folder_id, headers)

    @pytest.mark.qa
    def test_create_email_template_folder_with_parent_id_other_domain(self, create_email_template_folder,
                                                                      access_token_other):
        """
        This test is to assure that email template folder can't be created through
        parent_id of the other domain folder. Should return 400 bad request.
        """
        template_folder_id, template_folder_name = create_email_template_folder
        data = {'name': fake.sentence(), 'is_immutable': 1, 'parent_id': template_folder_id}
        CampaignsTestsHelpers.request_for_forbidden_error('post', EmailCampaignApiUrl.TEMPLATE_FOLDERS,
                                                          access_token_other, data)

    def test_get_email_template_folders_in_domain(self, headers):
        """
        In this test, we get email-template-folders in a domain
        """
        # Check without creating any template-folder
        response = requests.get(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, headers=headers)
        assert response.ok
        json_response = response.json()
        assert 'template_folders' in json_response
        assert len(json_response['template_folders']) == 0

        # Check with creating 5 template-folders
        for _ in xrange(5):
            data = {'name': fake.name(), 'is_immutable': 1}
            response = requests.post(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, data=json.dumps(data),
                                     headers=headers)
            assert response.ok
        response = requests.get(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, headers=headers)
        assert response.ok
        json_response = response.json()
        assert 'template_folders' in json_response
        assert len(json_response['template_folders']) == 5


class TestEmailTemplates(object):
    """
    Here are the tests of /v1/email-templates
    """
    URL = EmailCampaignApiUrl.TEMPLATES
    ENTITY = 'email_templates'

    def test_create_email_template(self, user_first, headers):
        """
        Here we create an email-template. Response should be OK.
        """
        # Add Email template
        template_data = data_to_create_email_template(headers, user_first, EMAIL_TEMPLATE_BODY)
        response = post_to_email_template_resource(headers, data=template_data)
        assert response.status_code == codes.CREATED
        assert response.json()
        json_response = response.json()
        assert 'id' in json_response

        # GET created email-template and assert on fields
        response = requests.get(EmailCampaignApiUrl.TEMPLATES, headers=headers)
        assert response.ok
        assert response.json()
        email_templates = response.json()[self.ENTITY]
        assert len(email_templates) == 1
        # Pick first record and assert expected field values
        assert_valid_template_object(email_templates[0], user_first.id, [json_response['id']], template_data['name'])

    def test_create_email_template_with_same_name(self, user_first, headers):
        """
        Test for creating email template with same name. It should get Bad request error.
        Here we first create email-template and then tries to create another email-template with same name.
        :param headers: For user authentication
        :param user_first: sample user
        """
        # Add Email template
        template_data = data_to_create_email_template(headers, user_first, EMAIL_TEMPLATE_BODY)
        template_data['name'] = fake.word() + str(datetime.datetime.utcnow().microsecond)
        response = post_to_email_template_resource(headers, data=template_data)
        assert response.status_code == codes.CREATED
        assert response.json()
        json_response = response.json()
        assert 'id' in json_response

        # Try to create another email-template with same name
        response = post_to_email_template_resource(headers, data=template_data)
        assert response.status_code == codes.BAD
        assert template_data['name'] in response.json()['error']['message']

    def test_get_email_templates(self, user_first, user_same_domain, user_from_diff_domain,
                                 headers, headers_same, headers_other):
        """
        Test for creating email template with different users of same domain.
        User should get both records while requesting email-templates.
        We create 2 email-templates in domain of user_first and 1 template in domain of user_from_diff_domain.
        user_first should get 2 records and user_from_diff_domain should get only 1 email-template.
        """
        expected_records_in_domain_1 = 2
        expected_records_in_domain_2 = 1
        # Add Email template by user_first
        add_email_template(headers, user_first)
        # Add Email template by user_same_domain
        add_email_template(headers_same, user_same_domain)
        # Add Email template by user of different domain
        add_email_template(headers_other, user_from_diff_domain)

        # Get all email-templates in user_first's domain
        response = requests.get(EmailCampaignApiUrl.TEMPLATES, headers=headers)
        assert response.ok
        assert response.json()
        email_templates = response.json()[self.ENTITY]
        assert len(email_templates) == expected_records_in_domain_1

        # Get all email-templates in user_from_diff_domain's domain
        response = requests.get(EmailCampaignApiUrl.TEMPLATES, headers=headers_other)
        assert response.ok
        assert response.json()
        email_templates = response.json()[self.ENTITY]
        assert len(email_templates) == expected_records_in_domain_2

    def test_create_and_get_email_template_without_name(self, user_first, headers):
        """
        Test for creating email template without passing name. The response should be Bad Request - 400
        because we are requesting to create an email template without passing the appropriate
        value for template name.
        :param user_first: sample user
        :param headers: For user authentication
        """
        # Empty template name
        template_name = ''
        data = data_to_create_email_template(headers, user_first, EMAIL_TEMPLATE_BODY)
        data['name'] = template_name
        response = post_to_email_template_resource(headers, data=data)
        assert response.status_code == requests.codes.BAD_REQUEST

    def test_create_template_without_email_body(self, user_first, headers):
        """
        Test for creating email template without passing email body. The response should be Bad Request - 400
        because template_body is mandatory for creating an email template.

        :param user_first: sample user
        :param headers: For user authentication
        """
        template_name = 'test_email_template%i' % datetime.datetime.now().microsecond
        data = data_to_create_email_template(headers, user_first)
        data['name'] = template_name
        response = post_to_email_template_resource(headers, data=data)
        assert response.status_code == requests.codes.BAD_REQUEST

    def test_get_with_paginated_response(self, headers, email_templates_bulk, user_first):
        """
        Here we test the paginated response of GET call on endpoint /v1/email-templates
        """
        # Test GET templates with 1 results per_page. It should get only 1 result
        response = requests.get(self.URL + '?per_page=1', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        assert len(json_resp) == 1
        received_template = json_resp[0]
        assert_valid_template_object(received_template, user_first.id, email_templates_bulk)

        # Test GET templates with 4 results per_page. It should get 4 results
        response = requests.get(self.URL + '?per_page=4', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick 4th result and assert valid response
        received_template = json_resp[3]
        assert_valid_template_object(received_template, user_first.id, email_templates_bulk)

        #  Test GET templates with 4 results per_page using page=2. It should get 4 results.
        response = requests.get(self.URL + '?per_page=4&page=2', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second result object and assert valid response
        received_template = json_resp[1]
        assert_valid_template_object(received_template, user_first.id, email_templates_bulk)

        # Test GET templates with 4 results per_page using page=3. It should get 2 results.
        response = requests.get(self.URL + '?per_page=4&page=3', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second record from the response.
        received_template = json_resp[1]
        assert_valid_template_object(received_template, user_first.id, email_templates_bulk)

        # Test GET templates with page = 4. No record should be found for given page params
        # in response as we have created 10 email-templates so far and we are using
        # per_page=4 and page=4.
        response = requests.get(self.URL + '?per_page=4&page=4', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=0, entity=self.ENTITY)


class TestEmailTemplate(object):
    """
    Here are the tests of /v1/email-templates/:id
    """
    URL = EmailCampaignApiUrl.TEMPLATE

    def test_get_email_template_via_id(self, user_first, headers_same, email_template):
        """
        Retrieve email_template via template's ID. We will create the email template using user_first
        and try to retrieve it using the template id returned in the response. user_same_domain with the same domain
        as the creator would be used to get the email template via id, verifying the users with same domain are
        allowed to access the templates created by fellow domain users. Response should be 200 (OK).
        """
        # Get email_template via template ID using token for 2nd user
        response = requests.get(url=self.URL % email_template['id'], headers=headers_same)
        assert response.status_code == requests.codes.OK
        resp_dict = response.json()['template']
        assert_valid_template_object(resp_dict, user_first.id, [email_template['id']], email_template['name'])

    def test_get_email_template_with_non_existing_id(self, email_template, headers_same):
        """
        Retrieve email_template via ID for which email template doesn't exist.We will create the email
        template using user_first and try to retrieve it by appending some random value to the template id returned
        in the response. user_same_domain with the same domain as the creator would be used to get the email template
        via id, as users with same domain are allowed to access the templates created by fellow domain users.
        Response should be 400 (NOT FOUND) as template id we are using to get is non-existent.
        """
        template_id = str(email_template['id']) + str(datetime.datetime.now().microsecond)
        # Get email_template via template ID
        response = requests.get(url=self.URL % template_id, headers=headers_same)
        assert response.status_code == requests.codes.NOT_FOUND

    def test_get_email_template_with_user_of_other_domain(self, email_template, headers_other):
        """
        Requesting an email-template with a user of some other domain. It should result in Forbidden error.
        """
        # Get email_template via template ID
        response = requests.get(url=self.URL % email_template['id'], headers=headers_other)
        assert response.status_code == requests.codes.FORBIDDEN

    def test_update_email_template(self, user_first, email_template, user_same_domain, access_token_same):
        """
        To update email template by other user in the same domain
        Response should be 200 (OK)
        """
        updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                                '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail' \
                                ' testing through script</p>\r\n</body>\r\n</html>\r\n'

        # Get email_template via template ID
        resp = update_email_template(email_template['id'], 'patch', access_token_same, user_same_domain.id,
                                     email_template['name'],
                                     updated_template_body, email_template['template_folder_id'],
                                     email_template['domain_id'])
        assert resp.status_code == requests.codes.OK
        resp_dict = resp.json()['template']
        assert_valid_template_object(resp_dict, user_first.id, [email_template['id']], email_template['name'],
                                     updated_template_body)

    def test_update_non_existing_email_template(self, email_template, user_same_domain, access_token_same):
        """
        Test : To update email template by other user in the same domain
        Expect: 404 - NOT FOUND
        """
        updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                                '\r\n<html>\r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>' \
                                '\r\n<p>test for update campaign mail testing through script</p>\r\n<' \
                                '/body>\r\n</html>\r\n'

        # Get email_template via template ID
        resp = update_email_template(str(email_template['id']) + str(datetime.datetime.now().microsecond),
                                     'patch', access_token_same, user_same_domain.id,
                                     email_template['name'],
                                     updated_template_body, '', email_template['template_folder_id'],
                                     email_template['is_immutable'])
        assert resp.status_code == requests.codes.NOT_FOUND

    def test_delete_email_template(self, access_token_same, email_template):
        """
        Tests deleting user's email template. Template should be deleted successfully returning
        204 (NO CONTENT) response.
        """
        resp = request_to_email_template_resource(access_token_same, 'delete', email_template['id'])
        assert resp.status_code == requests.codes.NO_CONTENT
        template_after_delete = UserEmailTemplate.get_by_id(email_template['id'])
        assert template_after_delete is None

    def test_delete_template_with_non_existing_template_id(self, email_template, access_token_same):
        """
        Tests deleting user's email template with non existing template_id. The response should be Not Found - 404
        as we are trying to delete a template which does not exist.
        """
        resp = request_to_email_template_resource(access_token_same, 'delete', str(email_template['id']) +
                                                  str(datetime.datetime.now().microsecond))
        assert resp.status_code == requests.codes.NOT_FOUND

    def test_delete_template_from_different_domain(self, email_template, access_token_other):
        """
        Tests deleting user's email template from different domain. The response should be Forbidden error - 403
        as a user with a different domain than template owner user is not allowed to delete the email template.
        """
        resp = request_to_email_template_resource(access_token_other, 'delete', email_template['id'])
        assert resp.status_code == requests.codes.FORBIDDEN
