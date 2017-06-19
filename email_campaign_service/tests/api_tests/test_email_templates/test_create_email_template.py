"""Test Email Template API: Contains tests for creating an Email Template.
"""
# Standard Library
import datetime

# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.common.models.email_campaign import EmailTemplateFolder
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  INVALID_REQUEST_BODY, INVALID_INPUT, MISSING_FIELD,
                                                                  DUPLICATE_TEMPLATE_NAME, TEMPLATE_FOLDER_FORBIDDEN,
                                                                  TEMPLATE_FOLDER_NOT_FOUND, NOT_NON_ZERO_NUMBER)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import (EMAIL_TEMPLATE_BODY, assert_valid_template_object,
                                                                  data_to_create_email_template,
                                                                  post_to_email_template_resource)


class TestEmailTemplates(object):
    """
    Here are the tests of /v1/email-templates
    """
    URL = EmailCampaignApiUrl.TEMPLATES
    ENTITY = 'email_templates'
    HTTP_METHOD = 'post'

    def test_creation_with_invalid_data(self, user_first, headers_for_email_templates,
                                        access_token_first_for_email_templates):
        """
        Trying to create email template with 1) no data and 2) Non-JSON data. It should result in invalid usage error.
        """
        template_data = data_to_create_email_template(headers_for_email_templates, user_first, EMAIL_TEMPLATE_BODY)
        for data in (template_data, None):
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                             access_token_first_for_email_templates,
                                                             data=data, is_json=False,
                                                             expected_error_code=INVALID_REQUEST_BODY[1])

    def test_create_email_template(self, user_first, headers_for_email_templates):
        """
        Here we create an email-template. Response should be OK.
        """
        # Add Email template
        template_data = data_to_create_email_template(headers_for_email_templates, user_first, EMAIL_TEMPLATE_BODY)
        response = post_to_email_template_resource(headers_for_email_templates, data=template_data)
        assert response.status_code == codes.CREATED
        json_response = response.json()
        assert 'id' in json_response

        # GET created email-template and assert on fields
        response = requests.get(EmailCampaignApiUrl.TEMPLATES, headers=headers_for_email_templates)
        assert response.ok
        email_templates = response.json()[self.ENTITY]
        assert len(email_templates) == 1
        # Pick first record and assert expected field values
        assert_valid_template_object(email_templates[0], user_first.id, [json_response['id']], template_data['name'])

    def test_creation_with_invalid_domain(self, access_token_other):
        """
        This test is to assure that email template folder can't be created through the user of domain other
        than Kaiser's. Should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL, access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_creation_with_duplicate_name(self, email_template, headers_other_for_email_templates,
                                          access_token_first_for_email_templates):
        """
        Test for creating email template with same name. Here we first create email-template and then tries
        to create another email-template with same name. It should result in Bad request error.
        We then create email-template with same name in some other domain, it should create the template with no error.
        """
        # Add Email template
        template_data = dict(body_html=EMAIL_TEMPLATE_BODY)
        template_data['name'] = email_template['name']
        # Try to create another email-template with same name in same domain
        CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                         access_token_first_for_email_templates, template_data,
                                                         expected_error_code=DUPLICATE_TEMPLATE_NAME[1])

        # Try to create another email-template with same name in some other domain.
        response = post_to_email_template_resource(headers_other_for_email_templates, data=template_data)
        assert response.status_code == codes.CREATED
        json_response = response.json()
        assert 'id' in json_response, 'Expecting id in the response'

    def test_creation_without_required_fields(self, access_token_first_for_email_templates):
        """
        Test for creating email template without passing required fields. The response should be Bad Request - 400
        because we are requesting to create an email template without passing the appropriate
        value for template name.
        """
        data = dict(name=fake.name(), body_html=EMAIL_TEMPLATE_BODY)
        for key, value in data.iteritems():
            missing_key = key
            missing_data = data.copy()
            del missing_data[key]
            response = CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL,
                                                                        access_token_first_for_email_templates,
                                                                        missing_data,
                                                                        expected_error_code=MISSING_FIELD[1])
            assert missing_key in response.json()['error']['message']

    def test_creation_with_invalid_data_types(self, access_token_first_for_email_templates):
        """
        This tries to create an email template with invalid string value of fields `name` and `body_html`,
        invalid boolean value for `is_immutable` and invalid integer value for `template_folder_id`.
        It should result in invalid usage error.
        """
        data = dict(name=fake.name(), body_html=EMAIL_TEMPLATE_BODY, template_folder_id=fake.random_int(),
                    is_immutable=0)
        for field in ('name', 'body_html'):
            CampaignsTestsHelpers.request_with_invalid_string(self.HTTP_METHOD, self.URL,
                                                              access_token_first_for_email_templates,
                                                              data.copy(), field=field,
                                                              expected_error_code=INVALID_INPUT[1])

        CampaignsTestsHelpers.request_with_invalid_integer(self.HTTP_METHOD, self.URL,
                                                           access_token_first_for_email_templates, data,
                                                           field='template_folder_id',
                                                           expected_error_code=INVALID_INPUT[1])

        del data['template_folder_id']
        CampaignsTestsHelpers.request_with_invalid_boolean(self.HTTP_METHOD, self.URL,
                                                           access_token_first_for_email_templates, data,
                                                           field='is_immutable', expected_error_code=INVALID_INPUT[1])

    def test_creation_with_not_owned_folder_id(self, headers_for_email_templates, user_first,
                                               access_token_other_for_email_templates):
        """
        This tries to create an email template with template_folder_id of some other domain.
        It should result in forbidden error.
        """
        template_data = data_to_create_email_template(headers_for_email_templates, user_first, EMAIL_TEMPLATE_BODY)
        response = post_to_email_template_resource(headers_for_email_templates, data=template_data)
        assert response.status_code == codes.CREATED
        json_response = response.json()
        assert 'id' in json_response

        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL,
                                                          access_token_other_for_email_templates, template_data,
                                                          expected_error_code=TEMPLATE_FOLDER_FORBIDDEN[1])

    def test_creation_with_non_existing_folder_id(self, access_token_other_for_email_templates):
        """
        This tries to create an email template with non-existing template_folder_id.
        It should result in resource not found error.
        """
        non_existing_folder_id = CampaignsTestsHelpers.get_non_existing_id(EmailTemplateFolder)
        template_data = dict(name=fake.name(), body_html=EMAIL_TEMPLATE_BODY,
                             template_folder_id=non_existing_folder_id)
        CampaignsTestsHelpers.request_for_resource_not_found_error(self.HTTP_METHOD, self.URL,
                                                                   access_token_other_for_email_templates,
                                                                   template_data,
                                                                   expected_error_code=TEMPLATE_FOLDER_NOT_FOUND[1])

    def test_creation_invalid_values_of_optional_fields(self, access_token_first_for_email_templates):
        template_data = dict(name=fake.name(), body_html=EMAIL_TEMPLATE_BODY)
