"""
Tests for ATS Accounts.
"""

from requests import codes

from ats_service.common.utils.test_utils import send_request
from ats_service.tests.test_utils import missing_field_test
from ats_service.app.api.ats_utils import ATS_ACCOUNT_FIELDS
from ats_service.common.routes import ATSServiceApiUrl


class TestATSAccounts(object):
    """
    """

    def test_post_account_without_auth(self, account_post_data):
        """
        """
        response = send_request('post', ATSServiceApiUrl.ACCOUNT, 'bad_bad_token', account_post_data)
        assert response.status_code == codes.UNAUTHORIZED

    # def test_post_account_with_missing_fields(self, account_post_data, token_first):
    #     """
    #     """
    #     for field in ATS_ACCOUNT_FIELDS:
    #         missing_field_test(account_post_data, field, token_first)
