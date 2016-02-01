"""
Test cases for CandidateViewResource/get()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, request_to_candidate_resource, request_to_candidates_resource,
    request_to_candidate_view_resource, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
# Custom erorrs
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


def test_user_without_appropriate_permission_to_view_candidate_info(access_token_first,
                                                                    user_first, talent_pool):
    """
    Test: User without "CAN_GET_CANDIDATES" permission to view candidate's view info
    Expect: 401
    """
    # Create Candidate
    AddUserRoles.add(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # sample_user views candidate
    request_to_candidate_resource(access_token_first, 'get', candidate_id)

    # Retrieve candidate's view information
    view_resp = request_to_candidate_view_resource(access_token_first, 'get', candidate_id)
    print response_info(view_resp)
    assert view_resp.status_code == 401


def test_retrieve_candidate_view_information(access_token_first, user_first, talent_pool):
    """
    Test: Get information pertaining to candidate from the CandidateView resource
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.add_and_get(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    candidate_id = create_resp.json()['candidates'][0]['id']

    request_to_candidate_resource(access_token_first, 'get', candidate_id) # view candidate
    request_to_candidate_resource(access_token_first, 'get', candidate_id) # view candidate again

    # Retrieve candidate's view information
    view_resp = request_to_candidate_view_resource(access_token_first, 'get', candidate_id)
    print response_info(view_resp)
    assert view_resp.status_code == 200
    assert len(view_resp.json()['candidate_views']) == 2
    assert view_resp.json()['candidate_views'][0]['candidate_id'] == candidate_id
    assert view_resp.json()['candidate_views'][1]['candidate_id'] == candidate_id
    assert view_resp.json()['candidate_views'][0]['user_id'] == user_first.id
    assert view_resp.json()['candidate_views'][1]['user_id'] == user_first.id


def test_all_users_from_domain_get_candidate_view(access_token_first, user_first, talent_pool,
                                                  user_same_domain, access_token_same):
    """
    Test: Users from candidate's domain to get candidate's view information
    Expect: 200
    """
    AddUserRoles.add_and_get(user=user_first)
    AddUserRoles.get(user=user_same_domain)

    # Create Candidate
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # user_first and user_same_domain viewing candidate
    request_to_candidate_resource(access_token_first, 'get', candidate_id)
    request_to_candidate_resource(access_token_same, 'get', candidate_id)

    # Retrieve candidate's view information
    view_resp = request_to_candidate_view_resource(access_token_first, 'get', candidate_id)
    view_resp_2 = request_to_candidate_view_resource(access_token_same, 'get', candidate_id)
    print response_info(view_resp)
    print response_info(view_resp_2)
    assert user_first.domain_id == user_same_domain.domain_id
    assert view_resp.status_code == 200 and view_resp_2.status_code == 200