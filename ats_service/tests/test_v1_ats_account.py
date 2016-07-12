"""
Tests for ATS Accounts.
"""

import json

from requests import codes

from ats_service.common.utils.test_utils import send_request
from ats_service.tests.test_utils import missing_field_test, empty_database
from ats_service.app.api.ats_utils import ATS_ACCOUNT_FIELDS
from ats_service.common.routes import ATSServiceApiUrl
from ats_service.common.tests.conftest import *

class TestATSAccounts(object):
    """
    Tests for the /v1/ats-accounts endpoint.
    """

    def setup_class(cls):
        """
        Prepare for testing with a database devoid of ATS values.
        """
        empty_database()

    def test_post_account_without_auth(self, account_post_data):
        """
        POST /v1/ats-accounts
        """
        response = send_request('post', ATSServiceApiUrl.ACCOUNTS, 'bad_bad_token', account_post_data)
        assert response.status_code == codes.UNAUTHORIZED

    def test_post_account_with_missing_fields(self, account_post_data, access_token_first):
        """
        POST /v1/ats-accounts
        """
        for field in ATS_ACCOUNT_FIELDS:
            data = account_post_data.copy()
            missing_field_test(data, field, access_token_first)

    def test_get_nonexistant_account(self, access_token_first):
        """
        GET /v1/ats-accounts
        """
        response = send_request('get', ATSServiceApiUrl.ACCOUNT % 12, access_token_first, {}, verify=False)
        assert response.status_code == codes.NOT_FOUND

    def test_create_ats_account(self, access_token_first, account_post_data):
        """
        POST /v1/ats-accounts Test creating an account
        GET  /v1/ats-accounts/id Test retrieving an account
        GET  /v1/ats Test getting the ATS entry created by adding the account

        Create an account then test that all table entries have been correctly added.
        """
        response = send_request('post', ATSServiceApiUrl.ACCOUNTS, access_token_first, account_post_data)
        assert response.status_code == codes.CREATED
        account_id = response.headers['location'].split('/')[-1]
        response = send_request('get', ATSServiceApiUrl.ACCOUNT % account_id, access_token_first, {}, verify=False)
        assert response.status_code == codes.OK
        values = json.loads(json.loads(response.text))
        assert values['credentials'] == account_post_data['ats_credentials']
        response = send_request('get', ATSServiceApiUrl.ATS, access_token_first, {}, verify=False)
        assert response.status_code == codes.OK
        values = json.loads(json.loads(response.text))
        assert len(values) == 1
        assert values[0]['login_url'] == account_post_data['ats_login']
