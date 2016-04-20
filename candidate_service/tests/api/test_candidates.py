"""
Test cases for candidate CRUD operations
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Custom Errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_errors

# Helper functions
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
from helpers import AddUserRoles
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info


class TestUpdateCandidateName(object):
    def test_update_first_name(self, user_first, access_token_first, talent_pool):
        """
        Test:  Update candidate's first name
        Expect: 200, candidate's full name should also be updated
        """
        # Create candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_full_name = get_resp.json()['candidate']['full_name']

        # Update candidate's first name
        data = {'candidates': [{'first_name': fake.first_name()}]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_full_name = get_resp.json()['candidate']['full_name']
        assert updated_full_name != candidate_full_name
        assert updated_full_name.startswith(data['candidates'][0]['first_name'])

    def test_update_middle_name(self, user_first, access_token_first, talent_pool):
        """
        Test:  Update candidate's middle name
        Expect: 200, candidate's full name should also be updated
        """
        # Create candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_full_name = get_resp.json()['candidate']['full_name']

        # Update candidate's middle name
        data = {'candidates': [{'middle_name': fake.first_name()}]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_full_name = get_resp.json()['candidate']['full_name']
        assert updated_full_name != candidate_full_name
        assert data['candidates'][0]['middle_name'] in updated_full_name

    def test_update_last_name(self, user_first, access_token_first, talent_pool):
        """
        Test:  Update candidate's last name
        Expect: 200, candidate's full name should also be updated
        """
        # Create candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_full_name = get_resp.json()['candidate']['full_name']

        # Update candidate's last name
        data = {'candidates': [{'last_name': fake.first_name()}]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_full_name = get_resp.json()['candidate']['full_name']
        assert updated_full_name != candidate_full_name
        assert updated_full_name.endswith(data['candidates'][0]['last_name'])
