"""Test Email Template API: Contains tests for GET Email Templates.
"""
# Standard Library
import datetime

# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import UserEmailTemplate
from email_campaign_service.common.custom_errors.campaign import TEMPLATES_FEATURE_NOT_ALLOWED, \
    INVALID_VALUE_OF_PAGINATION_PARAM
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.utils.test_utils import INVALID_PAGINATION_PARAMS
from email_campaign_service.tests.modules.handy_functions import (request_to_email_template_resource,
                                                                  EMAIL_TEMPLATE_BODY, update_email_template,
                                                                  add_email_template, assert_valid_template_object,
                                                                  data_to_create_email_template,
                                                                  post_to_email_template_resource)


class TestGETEmailTemplates(object):
    """
    Here are the tests of GET /v1/email-templates
    """
    URL = EmailCampaignApiUrl.TEMPLATES
    HTTP_METHOD = 'get'
    ENTITY = 'email_templates'

    def test_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_get_email_templates(self, headers_for_email_templates, headers_other_for_email_templates,
                                 email_templates_bulk, email_template_other):
        """
        Test for creating email template with different users of same domain.
        User should get both records while requesting email-templates.
        We create 2 email-templates in domain of user_first and 1 template in domain of user_from_diff_domain.
        user_first should get 2 records and user_from_diff_domain should get only 1 email-template.
        """
        expected_records_in_domain_1 = 10
        expected_records_in_domain_2 = 1

        # Get all email-templates in user_first's domain
        response = requests.get(self.URL, headers=headers_for_email_templates)
        assert response.ok, response.text
        email_templates = response.json()[self.ENTITY]
        assert len(email_templates) == expected_records_in_domain_1

        # Get all email-templates in other domain
        response = requests.get(self.URL, headers=headers_other_for_email_templates)
        assert response.ok, response.text
        email_templates = response.json()[self.ENTITY]
        assert len(email_templates) == expected_records_in_domain_2

    def test_get_email_templates_with_invalid_domain(self, access_token_other):
        """
        Non-Kaiser customer tries to access the API, it should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL,
                                                          access_token_other,
                                                          expected_error_code=TEMPLATES_FEATURE_NOT_ALLOWED[1])

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

    def test_get_with_invalid_pagination_params(self, access_token_first_for_email_templates):
        """
        Test GET API of getting email-templates using paginated response. Here we use invalid value of "per_page" to
        be 1) greater than maximum allowed value 2) Negative. It should result in invalid usage error.
        """
        for param in INVALID_PAGINATION_PARAMS:
            url = self.URL + param
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, url,
                                                             access_token_first_for_email_templates,
                                                             expected_error_code=INVALID_VALUE_OF_PAGINATION_PARAM[1])
