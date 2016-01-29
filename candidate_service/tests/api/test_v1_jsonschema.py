"""
Test cases for testing jsonschema validations
"""
# Candidate Service app instance
from candidate_service.candidate_app import app
# Conftest
from candidate_service.common.tests.conftest import *
# Helper functions
from helpers import (
    response_info, request_to_candidates_resource, AddUserRoles
)
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
        AddUserRoles.add(user=user_first)
        data = {}
        resp = request_to_candidates_resource(access_token_first, 'post', data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

        data['candidates'] = []
        resp = request_to_candidates_resource(access_token_first, 'post', data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

        data['candidates'] = [{}]
        resp = request_to_candidates_resource(access_token_first, 'post', data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

        data['candidates'] = [{'talent_pool_ids': {'add': [talent_pool.id]}}]
        resp = request_to_candidates_resource(access_token_first, 'post', data)
        print response_info(resp)
        assert resp.status_code == 201

