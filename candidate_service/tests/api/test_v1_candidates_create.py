"""
Test cases for CandidateResource/post()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import Candidate

# Conftest
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    create_same_candidate
)

######################## Candidate ########################
def test_create_candidate(sample_user, user_auth):
    """
    Test:   Create a new candidate and candidate's info
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    resp_dict = create_resp.json()
    print response_info(create_resp.request, resp_dict, create_resp.status_code)
    assert create_resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


def test_create_an_existing_candidate(sample_user, user_auth):
    """
    Test:   attempt to recreate an existing Candidate
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create same Candidate twice
    create_resp = create_same_candidate(token)

    resp_dict = create_resp.json()
    print response_info(create_resp.request, resp_dict, create_resp.status_code)
    assert create_resp.status_code == 400
    assert 'error' in resp_dict
