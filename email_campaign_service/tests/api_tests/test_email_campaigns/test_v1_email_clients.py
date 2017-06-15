"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

In this module, we have tests for following endpoints

    - POST /v1/email-clients
    - GET /v1/email-clients
    - GET /v1/email-clients/:id
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
from email_campaign_service.common.models.email_campaign import EmailClientCredentials
from email_campaign_service.common.custom_errors.campaign import (EMAIL_CLIENT_NOT_FOUND,
                                                                  EMAIL_CLIENT_FORBIDDEN)
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules import EMAIL_CLIENTS_ALL_FIELDS, EMAIL_CLIENTS_OPTIONAL_FIELDS
from email_campaign_service.tests.modules.handy_functions import (data_for_creating_email_clients,
                                                                  assert_email_client_fields)

__author__ = 'basit'


class TestCreateEmailClients(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.EMAIL_CLIENTS
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
            assert str(response.json()['id']) in response.headers['Location']

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
        invalid_key_values = [(key, CampaignsTestsHelpers.INVALID_STRINGS) for key in email_client_data]
        for key, values in invalid_key_values:
            for value in values:
                if key not in EMAIL_CLIENTS_SCHEMA['required'] and value in (None, '', '        '):
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

    def test_create_email_client_with_unexpected_field_in_data(self, access_token_first):
        """
        Here we try to make POST request with unexpected field in data. It should result in Bad request error.
        """
        for email_client_data in data_for_creating_email_clients():
            CampaignsTestsHelpers.test_api_with_with_unexpected_field_in_data(self.HTTP_METHOD, self.URL,
                                                                              access_token_first, email_client_data)

    def test_create_email_client_with_missing_field(self, headers):
        """
        This tests API with missing required and optional fields. It should result in Bad request error if required
        field is missing and should not get any error in case of missing optional field.
        """
        for email_client_data in data_for_creating_email_clients():
            for key in EMAIL_CLIENTS_ALL_FIELDS:
                value = email_client_data[key]
                del email_client_data[key]
                response = requests.post(self.URL, headers=headers, data=json.dumps(email_client_data))
                if key in EMAIL_CLIENTS_OPTIONAL_FIELDS:
                    assert response.status_code == codes.CREATED, response.text
                else:
                    assert response.status_code == codes.BAD, response.text
                email_client_data[key] = value


class TestGetEmailClients(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.EMAIL_CLIENTS
    HTTP_METHOD = 'get'

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_get_outgoing_clients(self, email_clients, headers, user_first):
        """
        We have created 3 email clients in the fixture email_clients.
        Here we GET only outoging email-clients from endpoint and assert valid response.
        """
        # GET outgoing email-clients
        response = requests.get(self.URL, headers=headers)
        assert response.ok
        assert response.json()
        email_clients_data = response.json()['email_client_credentials']
        assert len(email_clients_data) == 1
        assert_email_client_fields(email_clients_data[0], user_first.id)

    def test_get_incoming_clients(self, email_clients, headers, user_first):
        """
        We have created 3 email clients in the fixture email_clients.
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

    def test_get_invalid_client(self, email_clients, headers):
        """
        We have created 3 email clients in the fixture email_clients.
        Here we GET email-clients with invalid value of parameter "type".
        It should result in bad request error.
        """
        response = requests.get(self.URL + '?type=%s' % fake.word(), headers=headers)
        assert response.status_code == codes.BAD


class TestGetEmailClientsWithId(object):
    """
    Here are the tests of /v1/email-campaigns
    """
    URL = EmailCampaignApiUrl.EMAIL_CLIENT_WITH_ID
    HTTP_METHOD = 'get'

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int())

    def test_get_email_clients(self, email_clients, headers, user_first):
        """
        We have created 3 email clients in the fixture email_clients.
        Here we GET only email-clients from endpoint and assert valid response.
        """
        for email_client_id in email_clients:
            response = requests.get(self.URL % email_client_id, headers=headers)
            assert response.ok
            assert response.json()
            email_clients_data = response.json()['email_client_credentials']
            assert_email_client_fields(email_clients_data, user_first.id)

    def test_get_email_clients_from_other_user_of_same_domain(self, email_clients, headers_same, user_first):
        """
        We have created 3 email clients in the fixture email_clients.
        Here we GET only email-clients from endpoint using some other user of same domain and assert valid response.
        """
        for email_client_id in email_clients:
            response = requests.get(self.URL % email_client_id, headers=headers_same)
            assert response.ok
            assert response.json()
            email_clients_data = response.json()['email_client_credentials']
            assert_email_client_fields(email_clients_data, user_first.id)

    def test_get_email_clients_from_user_of_some_other_domain(self, email_clients, access_token_other):
        """
        We have created 3 email clients in the fixture email_clients.
        Here we GET only email-clients from endpoint using user of some other domain. It should result in
        Forbidden error.
        """
        for email_client_id in email_clients:
            CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD, self.URL % email_client_id,
                                                              access_token_other,
                                                              expected_error_code=EMAIL_CLIENT_FORBIDDEN[1])

    def test_get_email_clients_with_invalid_id(self, access_token_first):
        """
        Here we GET only email-clients from endpoint using 0 and non-existing id.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailClientCredentials,
                                                               self.HTTP_METHOD, self.URL, access_token_first,
                                                               expected_error_code=EMAIL_CLIENT_NOT_FOUND[1])
