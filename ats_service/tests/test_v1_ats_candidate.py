"""
Tests for ATS Candidates.
"""

import json

from requests import codes

from ats_service.common.utils.test_utils import send_request
from ats_service.tests.test_utils import (missing_field_test,
                                          empty_database,
                                          create_and_validate_candidate,
                                          create_and_validate_account,
                                          verify_nonexistant_candidate,
                                          link_candidates)
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

    def test_create_ats_candidate(self, access_token_first, account_post_data, candidate_post_data):
        """
        POST /v1/ats-candidates/:account_id
        GET /v1/ats-candidates/:candidate_id

        Create a candidate entry and validate that all table entries are correctly made.

        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        :param dict candidate_post_data: values for creating an ATS account
        """
        account_id = create_and_validate_account(access_token_first, account_post_data)
        create_and_validate_candidate(access_token_first, account_id, candidate_post_data)

    def test_delete_ats_candidate(self, access_token_first, account_post_data, candidate_post_data):
        """
        POST /v1/ats-candidates/:account_id
        GET /v1/ats-candidates/:account_id/:candidate_id
        DELETE /v1/ats-candidates/:account_id/:candidate_id

        Create an account, insert a candidate, then delete it and verify that it's gone.

        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        :param dict candidate_post_data: values for creating an ATS account
        """
        account_id = create_and_validate_account(access_token_first, account_post_data)
        candidate_id = create_and_validate_candidate(access_token_first, account_id, candidate_post_data)
        response = send_request('delete', ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id), access_token_first)
        assert response.status_code == codes.OK
        verify_nonexistant_candidate(access_token_first, account_id, candidate_id)

    def test_link_ats_candidate(self, access_token_first, account_post_data, candidate_post_data):
        """
        POST /v1/ats-candidates/:account_id
        POST /v1/ats-candidates/link/:candidate_id/:ats_candidate_id
        GET /v1/ats-candidates/:account_id/:candidate_id

        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        :param dict candidate_post_data: values for creating an ATS account
        """
        link_candidates(access_token_first, account_post_data, candidate_post_data)

    def test_unlink_ats_candidate(self, access_token_first, account_post_data, candidate_post_data):
        """
        POST /v1/ats-candidates/:account_id
        DELETE /v1/ats-candidates/link/:candidate_id/:ats_candidate_id
        GET /v1/ats-candidates/:account_id/:candidate_id

        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        :param dict candidate_post_data: values for creating an ATS account
        """
        account_id, gt_candidate_id, ats_candidate_id = link_candidates(access_token_first, account_post_data, candidate_post_data)
        response = send_request('delete', ATSServiceApiUrl.CANDIDATE_LINK % (gt_candidate_id, ats_candidate_id), access_token_first)
        assert response.status_code == codes.OK
        response = send_request('get', ATSServiceApiUrl.CANDIDATE % (account_id, ats_candidate_id), access_token_first, {}, verify=False)
        assert response.status_code == codes.OK
        values = json.loads(response.text)
        assert values['gt_candidate_id'] == None

    def test_update_ats_candidate(self, access_token_first, account_post_data, candidate_post_data):
        """
        POST /v1/ats-candidates/:account_id
        PUT /v1/ats-candidates/:account_id/:candidate_id
        GET /v1/ats-candidates/:account_id/:candidate_id

        Test updating an existing candidate's profile.

        :param str access_token_first: authentication token
        :param dict account_post_data: values for creating an ATS account
        :param dict candidate_post_data: values for creating an ATS account
        """
        account_id = create_and_validate_account(access_token_first, account_post_data)
        candidate_id = create_and_validate_candidate(access_token_first, account_id, candidate_post_data)
        response = send_request('get', ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id), access_token_first, {}, verify=False)
        assert response.status_code == codes.OK
        values = json.loads(response.text)
        new_value = '{ "some_other" : "json" }'
        values['profile_json'] = new_value
        response = send_request('put', ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id), access_token_first, values)
        assert response.status_code == codes.CREATED
        response = send_request('get', ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id), access_token_first, {}, verify=False)
        values = json.loads(response.text)
        assert values['profile_json'] == new_value
