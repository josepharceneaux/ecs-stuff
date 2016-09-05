"""Test Email Template API: Contains tests for Email Templates and Email Template Folders endpoints
"""
# Standard Library
import json
import datetime

# Third Party
import requests

# Application Specific
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import (ON, request_to_email_template_resource,
                                                                  template_body, get_template_folder,
                                                                  create_email_template, update_email_template,
                                                                  add_email_template, assert_valid_template_object,
                                                                  assert_valid_template_folder)


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
        response = requests.delete(url=EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
                                   data=json.dumps(data), headers=headers_same)
        assert response.status_code == requests.codes.NO_CONTENT


class TestEmailTemplates(object):
    """
    Here are the tests of /v1/email-templates
    """
    URL = EmailCampaignApiUrl.TEMPLATES
    ENTITY = 'email_templates'

    def test_create_and_get_email_template(self, user_first, headers):
        """
        Test for creating email template
        :param headers: For user authentication
        :param user_first: sample user
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        # Get all email-templates in user's domain
        response = requests.get(EmailCampaignApiUrl.TEMPLATES, headers=headers)
        assert response.ok
        assert response.json()
        # Pick first record
        email_template_obj = response.json()[self.ENTITY][0]
        # Assert expected field values
        assert_valid_template_object(email_template_obj, user_first.id, [template['template_id']],
                                     template['template_name'])

    def test_create_and_get_email_template_without_name(self, user_first, headers):
        """
        Test for creating email template without passing name. The response should be Bad Request - 400
        because we are requesting to create an email template without passing the appropriate
        value for template name.
        :param user_first: sample user
        :param headers: For user authentication
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = get_template_folder(headers)
        # Empty template name
        template_name = ''
        resp = create_email_template(headers, user_first.id, template_name, template_body(), template_name,
                                     is_immutable=ON, folder_id=template_folder_id)
        assert resp.status_code == requests.codes.BAD_REQUEST

    def test_create_template_without_email_body(self, user_first, headers):
        """
        Test for creating email template without passing email body. The response should be Bad Request - 400
        because template_body is mandatory for creating an email template.

        :param user_first: sample user
        :param headers: For user authentication
        """
        # Get Template Folder Id
        template_folder_id, template_folder_name = get_template_folder(headers)

        template_name = 'test_email_template%i' % datetime.datetime.now().microsecond

        # Pass empty email template body
        resp = create_email_template(headers, user_first.id, template_name, '',  # empty template body
                                     template_name, is_immutable=ON, folder_id=template_folder_id)
        assert resp.status_code == requests.codes.BAD_REQUEST

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

    def test_delete_email_template(self, user_first, headers, access_token_same):
        """
        Tests deleting user's email template. Template should be deleted successfully returning
        204 (NO CONTENT) response.

        :param user_first: user1
        :param headers: For user_first authorization
        :param access_token_same: For user_same_domain authorization
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        template_id = template['template_id']

        resp = request_to_email_template_resource(access_token_same, 'delete', template_id)
        assert resp.status_code == requests.codes.NO_CONTENT
        template_after_delete = UserEmailTemplate.get_by_id(template_id)
        assert template_after_delete is None

    def test_delete_template_with_non_existing_template_id(self, user_first, headers, access_token_same):
        """
        Tests deleting user's email template with non existing template_id. The response should be Not Found - 404
        as we are trying to delete a template which does not exist.

        :param user_first: we would use this to create the template.
        :param headers: For user authorization
        :param access_token_same: For user_same_domain authorization
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        template_id = template['template_id']

        resp = request_to_email_template_resource(access_token_same, 'delete', str(template_id) +
                                                  str(datetime.datetime.now().microsecond))
        assert resp.status_code == requests.codes.NOT_FOUND

    def test_delete_template_from_different_domain(self, user_first, headers, access_token_other):
        """
        Tests deleting user's email template from different domain. The response should be Forbidden error - 403
        as a user with a different domain than template owner user is not allowed to delete the email template.

        :param headers: For user authorization
        :param user_first: user whose token will be used to create the template.
        :param access_token_other: For user_from_diff_domain authorization
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        template_id = template['template_id']

        resp = request_to_email_template_resource(access_token_other, 'delete', template_id)
        assert resp.status_code == requests.codes.FORBIDDEN

    def test_get_email_template_via_id(self, user_first, headers, headers_same):
        """
        Retrieve email_template via template's ID. We will create the email template using user_first
        and try to retrieve it using the template id returned in the response. user_same_domain with the same domain
        as the creator would be used to get the email template via id, verifying the users with same domain are
        allowed to access the templates created by fellow domain users. Response should be 200 (OK).
        :param user_first: we would use this to create the template.
        :param headers: For user authorization
        :param headers_same: For user_same_domain authorization
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        template_id = template['template_id']
        url = EmailCampaignApiUrl.TEMPLATE % template_id
        # Get email_template via template ID using token for 2nd user
        response = requests.get(url=url, headers=headers_same)
        assert response.status_code == requests.codes.OK
        resp_dict = response.json()['template']
        assert isinstance(resp_dict, dict)
        assert resp_dict['id'] == template_id

    def test_get_email_template_with_non_existing_id(self, user_first, headers, headers_same):
        """
        Retrieve email_template via ID for which email template doesn't exist.We will create the email
        template using user_first and try to retrieve it by appending some random value to the template id returned
        in the response. user_same_domain with the same domain as the creator would be used to get the email template via id,
        as users with same domain are allowed to access the templates created by fellow domain users.
        Response should be 400 (NOT FOUND) as template id we are using to get is non-existent.
        :param user_first: we would use this to create the template.
        :param headers: For user authorization
        :param headers_same: For user_same_domain authorization
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        template_id = template['template_id']

        url = EmailCampaignApiUrl.TEMPLATE % template_id + str(datetime.datetime.now().microsecond)
        # Get email_template via template ID
        response = requests.get(url=url, headers=headers_same)
        assert response.status_code == requests.codes.NOT_FOUND

    def test_update_email_template(self, user_first, user_same_domain, headers, access_token_same):
        """
        To update email template by other user in the same domain
        Response should be 200 (OK)
        :param user_first: we would use this to create the template.
        :param user_same_domain: This is the user from same domain as user_first and would be used to update the
                template.
        :param headers: For user_first authorization
        :param access_token_same: For user_same_domain authorization
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())

        updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                                '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail' \
                                ' testing through script</p>\r\n</body>\r\n</html>\r\n'

        # Get email_template via template ID
        resp = update_email_template(template['template_id'], 'patch', access_token_same, user_same_domain.id,
                                     template['template_name'],
                                     updated_template_body, template['template_folder_id'],
                                     template['domain_id'])
        assert resp.status_code == requests.codes.OK
        resp_dict = resp.json()['template']
        print resp_dict
        assert resp_dict['body_html'] == updated_template_body

    def test_update_non_existing_email_template(self, user_first, user_same_domain, headers,
                                                access_token_same):
        """
        Test : To update email template by other user in the same domain
        :param user_first: we would use this to create the template.
        :param user_same_domain: This is the user from same domain as user_first and would be used to retrieve the
                template.
        :param headers: For user authorization
        Expect: 404 - NOT FOUND
        """
        # Add Email template
        template = add_email_template(headers, user_first, template_body())
        template_id = template['template_id']

        updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                                '\r\n<html>\r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>' \
                                '\r\n<p>test for update campaign mail testing through script</p>\r\n<' \
                                '/body>\r\n</html>\r\n'

        # Get email_template via template ID
        resp = update_email_template(str(template_id) + str(datetime.datetime.now().microsecond),
                                     'patch', access_token_same, user_same_domain.id,
                                     template['template_name'],
                                     updated_template_body, '', template['template_folder_id'],
                                     template['is_immutable'])
        assert resp.status_code == requests.codes.NOT_FOUND
