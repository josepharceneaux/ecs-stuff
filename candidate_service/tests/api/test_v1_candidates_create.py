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
    create_same_candidate, generate_single_candidate_data
)

######################## Candidate ########################
def test_create_candidate(sample_user, user_auth):
    """
    Test:   Create a new candidate and candidate's info
    Expect: 201
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


def test_create_candidate_and_retrieve_it(sample_user, user_auth):
    """
    Test:   Create a Candidate and retrieve it. Ensure that the data sent in for creating the
            Candidate is identical to the data obtained from retrieving the Candidate
            minus id-keys
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    data = generate_single_candidate_data()
    print "data = %s" % data
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)

    # Retreive Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id)
    # TODO: get-object must be identical to data after removing all ids & none values


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
