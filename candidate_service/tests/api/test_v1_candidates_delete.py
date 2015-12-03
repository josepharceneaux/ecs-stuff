"""
Test cases for CandidateResource/delete()
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
    delete_to_candidate_resource, patch_to_candidate_resource
)


######################## Candidate ########################
def test_delete_candidate(sample_user, user_auth):
    """
    Test:   "Delete" a Candidate by setting is_web_hidden to True, and then retrieve Candidate
    Expect: 404, Not Found error
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete (hide) Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = delete_to_candidate_resource(token, candidate_id)
    print response_info(resp.request, resp.json(), resp.status_code)

    # Retrieve Candidate
    get_resp = get_from_candidate_resource(token, candidate_id)
    print response_info(get_resp.request, get_resp.json(), get_resp.status_code)

    assert get_resp.status_code == 404


######################## CandidateAddress ########################
def test_remove_candidate_address(sample_user, user_auth):
    """
    Test:   Remove Candidate's CandidateAddress from db
    Expect: 204, Candidate's addresses must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_addresses = candidate_dict['addresses']

    # Number of Candidate's addresses
    candidate_addresses_count = len(candidate_addresses)

    # Remove one of Candidate's addresses
    updated_resp = delete_to_candidate_resource(token, candidate_id,
                                                address_id=candidate_addresses[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['addresses']) == candidate_addresses_count - 1


def test_remove_all_of_candidates_addresses(sample_user, user_auth):
    """
    Test:   Remove all of candidate's addresses from db
    Expect: 204, Candidate should not have any addresses left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Remove all of Candidate's addresses
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = delete_to_candidate_resource(token, candidate_id, can_addresses=True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['addresses']) == 0





