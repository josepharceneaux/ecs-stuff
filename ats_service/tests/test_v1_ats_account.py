"""
Tests for ATS Accounts.
"""

from requests import codes

from ats_service.common.utils.test_utils import send_request
from ats_service.tests.test_utils import missing_field_test, empty_database, create_and_validate_account, verify_nonexistant_account
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

        Test authentication failure.
        
        :param dict account_post_data: values for creating an ATS account
        """
        response = send_request('post', ATSServiceApiUrl.ACCOUNTS, 'bad_bad_token', account_post_data)
        assert response.status_code == codes.UNAUTHORIZED

    def test_post_account_with_missing_fields(self, account_post_data, access_token_first):
        """
        POST /v1/ats-accounts

        Test creating account with missing data.
        
        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        """
        for field in ATS_ACCOUNT_FIELDS:
            data = account_post_data.copy()
            missing_field_test(data, field, access_token_first)

    def test_get_nonexistant_account(self, access_token_first):
        """
        GET /v1/ats-accounts

        Test error from retrieving non-existant account.
        
        :param str access_token_first: authentication token
        """
        verify_nonexistant_account(access_token_first, 12)

    def test_create_ats_account(self, access_token_first, account_post_data):
        """
        POST /v1/ats-accounts Test creating an account
        GET  /v1/ats-accounts/id Test retrieving an account
        GET  /v1/ats Test getting the ATS entry created by adding the account

        Create an account then test that all table entries have been correctly added.
        
        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        """
        create_and_validate_account(access_token_first, account_post_data)

    def test_delete_ats_account(self, access_token_first, account_post_data):
        """
        POST /v1/ats-accounts Test creating an account
        DELETE /v1/ats-accounts/:account_id

        Verify deletion of account.
        
        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        """
        account_id = create_and_validate_account(access_token_first, account_post_data)
        response = send_request('delete', ATSServiceApiUrl.ACCOUNT % account_id, access_token_first)
        assert response.status_code == codes.OK
        values = json.loads(response.text)
        assert values['delete'] == 'success'
        verify_nonexistant_account(access_token_first, account_id)

    def test_update_ats_account(self, access_token_first, account_post_data):
        """
        POST /v1/ats-accounts Test creating an account
        PUT /v1/ats-accounts/:account_id Test updating an account
        GET /v1/ats-accounts/:account_id Test fetching an account

        Update and verify new data of account.

        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        """
        account_id = create_and_validate_account(access_token_first, account_post_data)
        key = 'ats_homepage'
        value =  'https://someotherhost.com/authenticate'
        new_data = { key : value }
        response = send_request('put', ATSServiceApiUrl.ACCOUNT % account_id, access_token_first, new_data)
        assert response.status_code == codes.CREATED
        response = send_request('get', ATSServiceApiUrl.ACCOUNT % account_id, access_token_first, {}, verify=False)
        assert response.status_code == codes.OK
        # TODO: Normalize service output text between endpoints
        values = json.loads(response.text)
        assert values[key] == value
