"""
Tests for ATS Candidates.
"""

import json

from requests import codes

from ats_service.common.utils.test_utils import send_request
from ats_service.tests.test_utils import missing_field_test, empty_database
from ats_service.app.api.ats_utils import ATS_ACCOUNT_FIELDS
from ats_service.common.routes import ATSServiceApiUrl
from ats_service.common.tests.conftest import *

class TestATSCandidates(object):
    """
    Tests for the /v1/ats-candidates endpoint.
    """

    def setup_class(cls):
        """
        Prepare for testing with a database devoid of ATS values.
        """
        empty_database()

    def test_create_ats_candidate(self, access_token_first, account_post_data):
        """
        """
        pass

    def test_delete_ats_candidate(self, access_token_first, account_post_data):
        """
        """
        pass

    def test_link_ats_candidate(self, access_token_first, account_post_data):
        """
        """
        pass

    def test_update_ats_candidate(self, access_token_first, account_post_data):
        """
        """
        pass
