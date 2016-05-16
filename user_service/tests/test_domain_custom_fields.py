# User Service app instance
from user_service.user_app import app

# Conftest
from user_service.common.tests.conftest import *

# Helper functions
from user_service.common.routes import UserServiceApiUrl
from user_service.common.utils.test_utils import send_request, response_info


class TestCreateDomainCustomFields(object):
    CREATED = 201
    INVALID = 400
    UNAUTHORIZED = 401
    URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS

    def test_add_custom_fields_without_access_token(self):
        """
        Test:  Access end point without an access token
        """
        resp = send_request('post', self.URL, None, {})
        print response_info(resp)
        assert resp.status_code == self.UNAUTHORIZED

    def test_add_custom_fields_with_whitespaced_name(self, access_token_first):
        """
        Test: Attempt to create a custom field with empty
        """
        data = {'custom_fields': [{'name': '   '}]}
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.INVALID

    def test_add_custom_fields_to_domain(self, access_token_first):
        """
        Test:  Add custom fields to domain
        """
        data = {'custom_fields': [{'name': str(uuid.uuid4())[:5]}, {'name': str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED
        assert len(create_resp.json()['custom_fields']) == len(data['custom_fields'])
        assert 'id' in create_resp.json()['custom_fields'][0]

    def test_add_duplicate_custom_fields_to_domain(self, access_token_first):
        """
        Test:  Add identical custom fields to the same domain
        Expect:  201, but only one should be created
        """
        name = str(uuid.uuid4())[:5]
        data = {'custom_fields': [{'name': name}, {'name': name}]}
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED
        assert len(create_resp.json()['custom_fields']) == len(data['custom_fields']) - 1
        assert 'id' in create_resp.json()['custom_fields'][0]


class TestGetDomainCustomFields(object):
    OK = 200
    UNAUTHORIZED = 401
    URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS

    def test_get_custom_fields_without_access_token(self):
        """
        Test:  Access end point without an access token
        """
        resp = send_request('get', self.URL, None)
        print response_info(resp)
        assert resp.status_code == self.UNAUTHORIZED

    def test_get_custom_fields_to_domain(self, access_token_first):
        """
        Test:  Retrieve domain custom fields
        """
        data = {'custom_fields': [{'name': str(uuid.uuid4())[:5]}, {'name': str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)

        get_resp = send_request('get', self.URL, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['custom_fields']) == len(data['custom_fields'])