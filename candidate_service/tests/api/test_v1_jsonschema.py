"""
Test cases for testing json schema validations
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestSchemaValidationPost(object):
    def test_schema_validation(self, access_token_first, user_first, talent_pool):
        """
        Test: Schema validations for CandidatesResource/post()
        Expect: 400 unless if a dict of CandidateObject is provided with at least
                one talent_pool.id
        """
        # Create Candidate
        AddUserRoles.add(user_first)
        data = {}
        resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

        data['candidates'] = []
        resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

        data['candidates'] = [{}]
        resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

        data['candidates'] = [{'talent_pool_ids': {'add': [talent_pool.id]}}]
        resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 201


class TestSchemaValidationPatch(object):
    def test_data_validations(self, access_token_first, user_first):
        """
        Test:   Validate json data
        Expect: 400
        """
        AddUserRoles.edit(user_first)
        data = {'candidate': [{}]}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400

        data = {'candidates': {}}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400

        data = {'candidates': [{}]}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400

        data = {'candidates': [{'id': 5, 'phones': [{}]}]}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400

