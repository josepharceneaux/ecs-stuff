"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    1 - POST /v1/email-clients
"""
# Standard Library
import json

# Third Party
import requests
from requests import codes

# Application Specific
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.json_schema.email_clients import EMAIL_CLIENTS_SCHEMA
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import data_for_creating_email_clients

__author__ = 'basit'


class TestCreateEmailClients(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.CLIENTS
    HTTP_METHOD = 'post'

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_create_email_client_with_valid_data(self, headers):
        """
        Here we try to add server-side email-client with valid data. It should not get any error.
        """
        for email_client_data in data_for_creating_email_clients():
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.ok
            assert 'id' in response.json()

    def test_create_email_client_with_invalid_type(self, headers):
        """
        Here we try to add server-side email-client with invalid type of server. It should result in
        invalid usage error.
        """
        for email_client_data in data_for_creating_email_clients():
            email_client_data['type'] = fake.word()
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.status_code == codes.BAD

    def test_create_email_client_with_invalid_email_format(self, headers):
        """
        Here we try to add server-side email-client with invalid email-address. It should result in
        invalid usage error.
        """
        for email_client_data in data_for_creating_email_clients():
            email_client_data['email'] = 'Invalid Email Address:%s ' % fake.uuid4()
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.status_code == codes.BAD

    def test_create_email_client_with_invalid_host(self, headers):
        """
        Here we try to add server-side email-client with invalid email-address. It should result in
        invalid usage error.
        """
        for email_client_data in data_for_creating_email_clients():
            email_client_data['host'] = fake.word()
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.status_code == codes.BAD

    def test_create_email_client_with_invalid_credentials(self, headers):
        """
        Here we try to add server-side email-client with invalid email-address. It should result in
        invalid usage error.
        """
        for email_client_data in data_for_creating_email_clients():
            email_client_data['password'] = fake.password()
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.status_code == codes.BAD

    def test_with_invalid_format_of_fields(self, headers):
        """
        In this test, we will test endpoint with invalid format of fields which will cause 400 error.
        """
        email_client_data = data_for_creating_email_clients()[0]
        invalid_key_values = [(key, CampaignsTestsHelpers.INVALID_STRING) for key in email_client_data]
        for key, values in invalid_key_values:
            for value in values:
                if key not in EMAIL_CLIENTS_SCHEMA['required'] and value in (None, '', '      '):
                    pass
                else:
                    data = email_client_data.copy()
                    data[key] = value
                    response = requests.post(self.URL, headers=headers, data=json.dumps(data))
                    assert response.status_code == requests.codes.BAD_REQUEST, 'data is:%s' % data

    def test_duplicate_email_client(self, headers):
        """
        Here we try to save duplicate email-client which should cause 400 error.
        """
        for email_client_data in data_for_creating_email_clients():
            # It should create first time
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.ok
            assert 'id' in response.json()

            # Try to create duplicate
            response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
            assert response.status_code == requests.codes.BAD
