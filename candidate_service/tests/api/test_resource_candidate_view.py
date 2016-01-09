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


def test_retrieve_candidate_view_information(sample_user, user_auth):
    """
    Test: Get information pertaining to candidate from the CandidateView resource
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

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