"""
Test cases for CandidateViewResource/get()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User

# Conftest
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    request_to_candidate_view_resource
)
from candidate_service.common.utils.handy_functions import add_role_to_test_user


# TODO: Uncomment test once user-roles are implemented for the candidates resources
# def test_user_without_appropriate_permission_to_view_candidate_info(sample_user, user_auth):
#     """
#     Test: User without "CAN_VIEW_CANDIDATES" permission to view candidate's view info
#     Expect: 401
#     :type sample_user:      User
#     :type user_auth:        UserAuthentication
#     """
#     # Access token
#     token = user_auth.get_auth_token(sample_user, True)['access_token']
#
#     # Create Candidate
#     create_resp = post_to_candidate_resource(token)
#     candidate_id = create_resp.json()['candidates'][0]['id']
#
#     get_from_candidate_resource(token, candidate_id)  # sample_user views candidate
#
#     # Retrieve candidate's view information
#     view_resp = request_to_candidate_view_resource(token, 'get', candidate_id)
#     print response_info(view_resp)
#     assert view_resp.status_code == 401


def test_retrieve_candidate_view_information(sample_user, user_auth):
    """
    Test: Get information pertaining to candidate from the CandidateView resource
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Access token & Appropriate role to sample_user
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    add_role_to_test_user(sample_user, ['CAN_GET_CANDIDATES_VIEW_INFO'])

    # Create Candidate
    create_resp = post_to_candidate_resource(token)
    candidate_id = create_resp.json()['candidates'][0]['id']

    get_from_candidate_resource(token, candidate_id) # view candidate
    get_from_candidate_resource(token, candidate_id) # view candidate again

    # Retrieve candidate's view information
    view_resp = request_to_candidate_view_resource(token, 'get', candidate_id)
    print response_info(view_resp)
    assert view_resp.status_code == 200
    assert len(view_resp.json()['candidate_views']) == 2
    assert view_resp.json()['candidate_views'][0]['candidate_id'] == candidate_id
    assert view_resp.json()['candidate_views'][1]['candidate_id'] == candidate_id
    assert view_resp.json()['candidate_views'][0]['user_id'] == sample_user.id
    assert view_resp.json()['candidate_views'][1]['user_id'] == sample_user.id


def test_all_users_from_domain_get_candidate_view(sample_user, sample_user_2, user_auth):
    """
    Test: Users from candidate's domain to get candidate's view information
    Expect: 200
    :type sample_user:      User
    :type sample_user_2:    User
    :type user_auth:        UserAuthentication
    """
    # Access tokens & Appropriate role to sample_user and sample_user_2
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']
    add_role_to_test_user(sample_user, ['CAN_GET_CANDIDATES_VIEW_INFO'])
    add_role_to_test_user(sample_user_2, ['CAN_GET_CANDIDATES_VIEW_INFO'])

    # Create Candidate
    create_resp = post_to_candidate_resource(token_1)
    candidate_id = create_resp.json()['candidates'][0]['id']

    get_from_candidate_resource(token_1, candidate_id)  # sample_user views candidate
    get_from_candidate_resource(token_2, candidate_id)  # sample_user_2 views candidate

    # Retrieve candidate's view information
    view_resp = request_to_candidate_view_resource(token_1, 'get', candidate_id)
    view_resp_2 = request_to_candidate_view_resource(token_2, 'get', candidate_id)
    print response_info(view_resp)
    print response_info(view_resp_2)
    assert sample_user.domain_id == sample_user_2.domain_id
    assert view_resp.status_code == 200 and view_resp_2.status_code == 200