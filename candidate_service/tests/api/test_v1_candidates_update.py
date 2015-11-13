"""
Test cases for CandidateResource/delete()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import Candidate

# Conftest
from common.tests.conftest import UserAuthentication
from common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    update_candidate, patch_to_candidate_resource
)

########################################################################
########################################################################
def test_update_candidate(sample_user, user_auth):
    """
    Test:   update an existing candidate
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Update Candidate
    resp = update_candidate(access_token=auth_token_row['access_token'])

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 200
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


def test_update_candidate_without_id(sample_user, user_auth):
    """
    Test:   attempt to update a candidate without providing the ID
    Expect: 400
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(
        sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    resp = post_to_candidate_resource(access_token=token)

    # Update Candidate's first_name
    data = {'candidate': {'first_name': 'larry'}}
    resp = patch_to_candidate_resource(token, data)

    print response_info(resp.request, resp.json(), resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp.json()


def test_update_candidate_names(sample_user, user_auth):
    """
    Test:   update candidate's first, middle, and last names
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(
        sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(access_token=token)

    # Update Candidate's first_name
    candidate_id = create_resp.json()['candidates'][0]['id']
    data = {'candidate':
                {'id': candidate_id, 'first_name': 'larry',
                 'middle_name': 'james', 'last_name': 'david'}
            }
    update_resp = patch_to_candidate_resource(token, data)

    print response_info(update_resp.request, update_resp.json(),
                        update_resp.status_code)
    assert candidate_id == update_resp.json()['candidates'][0]['id']

    # Retrieve Candidate
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()

    # Assert on updated field
    assert candidate_dict['candidate']['full_name'] == 'Larry David'
