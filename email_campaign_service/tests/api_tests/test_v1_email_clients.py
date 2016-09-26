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
from email_campaign_service.tests.modules.handy_functions import (data_for_creating_email_clients,
                                                                  assert_email_client_fields)

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


class TestGetEmailClients(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.CLIENTS
    HTTP_METHOD = 'get'

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_get_outgoing_clients(self, create_email_clients, headers, user_first):
        """
        We have created 3 email clients in the fixture create_email_clients.
        Here we GET only outoging email-clients from endpoint and assert valid response.
        """
        # GET outgoing email-clients
        response = requests.get(self.URL, headers=headers)
        assert response.ok
        assert response.json()
        email_clients_data = response.json()['email_client_credentials']
        assert len(email_clients_data) == 1
        assert_email_client_fields(email_clients_data[0], user_first.id)

    def test_get_incoming_clients(self, create_email_clients, headers, user_first):
        """
        We have created 3 email clients in the fixture create_email_clients.
        Here we GET only incoming email-clients from endpoint and assert valid response.
        """
        # GET incoming email-clients
        response = requests.get(self.URL + '?type=incoming', headers=headers)
        assert response.ok
        assert response.json()
        email_clients_data = response.json()['email_client_credentials']
        assert len(email_clients_data) == 2
        for email_client_data in email_clients_data:
            assert_email_client_fields(email_client_data, user_first.id)

    def test_with_no_client_created(self, headers):
        """
        We have not created any email-client for this test.
        Here we GET email-clients from endpoint and assert we do not get any object from API.
        """
        response = requests.get(self.URL, headers=headers)
        assert response.ok
        assert response.json()
        email_client_data = response.json()['email_client_credentials']
        assert len(email_client_data) == 0

    def test_get_invalid_client(self, create_email_clients, headers):
        """
        We have created 3 email clients in the fixture create_email_clients.
        Here we GET email-clients with invalid value of parameter "type".
        It should result in bad request error.
        """
        response = requests.get(self.URL + '?type=%s' % fake.word(), headers=headers)
        assert response.status_code == codes.BAD

class TestEmailCampaignWithEmailClient(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.CLIENTS
    HTTP_METHOD = 'post'
