"""
Tests for ATS Accounts.
"""

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
        empty_database()

    def test_post_account_without_auth(self, account_post_data):
        """
        """
        response = send_request('post', ATSServiceApiUrl.ACCOUNTS, 'bad_bad_token', account_post_data)
        assert response.status_code == codes.UNAUTHORIZED

    def test_post_account_with_missing_fields(self, account_post_data, access_token_first):
        """
        """
        for field in ATS_ACCOUNT_FIELDS:
            data = account_post_data.copy()
            missing_field_test(data, field, access_token_first)

    # def test_get_nonexistant_account(access_token_first):
    #     """
    #     """
    #     response = send_request('get', ATSServiceApiUrl.ACCOUNT % 12, access_token_first, '', verify=False)
    #     assert True
