"""
Tests for ATS Accounts.
"""


from ats_service.tests.test_utils import missing_field_test
from ats_service.app.api.ats_utils import ATS_ACCOUNT_FIELDS


class TestATSAccounts(object):
    """
    """

    def test_post_account_with_missing_fields(self, account_post_data, token_first):
        """
        """
        for field in ATS_ACCOUNT_FIELDS:
            missing_field_test(account_post_data, field, token_first)
