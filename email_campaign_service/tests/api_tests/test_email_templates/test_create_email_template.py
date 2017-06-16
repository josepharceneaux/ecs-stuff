"""Test Email Template API: Contains tests for creating an Email Template.
"""
# Standard Library
import datetime

# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.custom_errors.campaign import (TEMPLATES_FEATURE_NOT_ALLOWED,
                                                                  INVALID_REQUEST_BODY)
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

    def test_create_email_template_with_invalid_domain(self, access_token_other):
        """
        This test is to assure that email template folder can't be created through the user of domain other
        than Kaiser's. Should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error('post', EmailCampaignApiUrl.TEMPLATES,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

    def test_create_email_template_with_same_name(self, user_first, headers_for_email_templates,
                                                  headers_other_for_email_templates, user_from_diff_domain):
        """
        Test for creating email template with same name. Here we first create email-template and then tries
        to create another email-template with same name. It should result in Bad request error.
        We then create email-template with same name in some other domain, it should create the template with no error.
        """
        # Add Email template
        template_data = data_to_create_email_template(headers_for_email_templates, user_first, EMAIL_TEMPLATE_BODY)
        template_name = fake.word() + str(datetime.datetime.utcnow().microsecond)
        template_data['name'] = template_name
        response = post_to_email_template_resource(headers_for_email_templates, data=template_data)
        assert response.status_code == codes.CREATED
        json_response = response.json()
        assert 'id' in json_response

        # Try to create another email-template with same name
        response = post_to_email_template_resource(headers_for_email_templates, data=template_data)
        assert response.status_code == codes.BAD
        assert template_name in response.json()['error']['message']

        # Try to create another email-template with same name in some other domain.
        template_data = data_to_create_email_template(headers_other_for_email_templates, user_from_diff_domain,
                                                      EMAIL_TEMPLATE_BODY)
        template_data['name'] = template_name
        response = post_to_email_template_resource(headers_other_for_email_templates, data=template_data)
        assert response.status_code == codes.CREATED
        json_response = response.json()
        assert 'id' in json_response, 'Expecting id in the response'

    def test_create_and_get_email_template_without_name(self, user_first, headers_for_email_templates):
        """
        Test for creating email template without passing name. The response should be Bad Request - 400
        because we are requesting to create an email template without passing the appropriate
        value for template name.
        """
        # Empty template name
        template_name = ''
        data = data_to_create_email_template(headers_for_email_templates, user_first, EMAIL_TEMPLATE_BODY)
        data['name'] = template_name
        response = post_to_email_template_resource(headers_for_email_templates, data=data)
        assert response.status_code == requests.codes.BAD_REQUEST

    def test_create_template_without_email_body(self, user_first, headers_for_email_templates):
        """
        Test for creating email template without passing email body. The response should be Bad Request - 400
        because template_body is mandatory for creating an email template.
        """
        template_name = 'test_email_template%i' % datetime.datetime.now().microsecond
        data = data_to_create_email_template(headers_for_email_templates, user_first)
        data['name'] = template_name
        response = post_to_email_template_resource(headers_for_email_templates, data=data)
        assert response.status_code == requests.codes.BAD_REQUEST
