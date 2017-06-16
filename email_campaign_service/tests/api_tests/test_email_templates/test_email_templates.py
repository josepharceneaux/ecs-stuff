"""
    Test Email Template API: Contains tests for Email Template.
"""
# Standard Library
import datetime

# Third Party
import requests

# Application Specific
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.tests.modules.handy_functions import (request_to_email_template_resource,
                                                                  update_email_template, assert_valid_template_object)


class TestEmailTemplate(object):
    """
    Here are the tests of /v1/email-templates/:id
    """
    URL = EmailCampaignApiUrl.TEMPLATE

    def test_get_email_template_via_id(self, user_first, headers_same_for_email_templates, email_template):
        """
        Retrieve email_template via template's ID. We will create the email template using user_first
        and try to retrieve it using the template id returned in the response. user_same_domain with the same domain
        as the creator would be used to get the email template via id, verifying the users with same domain are
        allowed to access the templates created by fellow domain users. Response should be 200 (OK).
        """
        # Get email_template via template ID using token for 2nd user
        response = requests.get(url=self.URL % email_template['id'], headers=headers_same_for_email_templates)
        assert response.status_code == requests.codes.OK
        resp_dict = response.json()['template']
        assert_valid_template_object(resp_dict, user_first.id, [email_template['id']], email_template['name'])

    def test_get_email_template_with_non_existing_id(self, email_template, headers_same_for_email_templates):
        """
        Retrieve email_template via ID for which email template doesn't exist.We will create the email
        template using user_first and try to retrieve it by appending some random value to the template id returned
        in the response. user_same_domain with the same domain as the creator would be used to get the email template
        via id, as users with same domain are allowed to access the templates created by fellow domain users.
        Response should be 400 (NOT FOUND) as template id we are using to get is non-existent.
        """
        template_id = str(email_template['id']) + str(datetime.datetime.now().microsecond)
        # Get email_template via template ID
        response = requests.get(url=self.URL % template_id, headers=headers_same_for_email_templates)
        assert response.status_code == requests.codes.NOT_FOUND

    def test_get_email_template_with_user_of_other_domain(self, email_template, headers_other):
        """
        Requesting an email-template with a user of some other domain. It should result in Forbidden error.
        """
        # Get email_template via template ID
        response = requests.get(url=self.URL % email_template['id'], headers=headers_other)
        assert response.status_code == requests.codes.FORBIDDEN

    def test_update_email_template(self, user_first, email_template, headers_same_for_email_templates,
                                   user_same_domain, access_token_same):
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

    def test_update_non_existing_email_template(self, email_template, headers_same_for_email_templates,
                                                user_same_domain, access_token_same):
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

    def test_delete_email_template(self, headers_same_for_email_templates, access_token_same, email_template):
        """
        Tests deleting user's email template. Template should be deleted successfully returning
        204 (NO CONTENT) response.
        """
        resp = request_to_email_template_resource(access_token_same, 'delete', email_template['id'])
        assert resp.status_code == requests.codes.NO_CONTENT
        template_after_delete = UserEmailTemplate.get_by_id(email_template['id'])
        assert template_after_delete is None

    def test_delete_template_with_non_existing_template_id(self, email_template, headers_same_for_email_templates,
                                                           access_token_same):
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
