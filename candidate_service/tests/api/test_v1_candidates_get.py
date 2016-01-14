"""
Test cases for CandidateResource/get()
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
    response_info, post_to_candidate_resource, get_from_candidate_resource, check_for_id,
    request_to_candidates_resource
)

######################## Candidate ########################
def test_get_candidate_without_authed_user(sample_user, user_auth):
    """
    Test:   Attempt to retrieve candidate with no access token
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)
    resp_dict = create_resp.json()
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = resp_dict['candidates'][0]['id']
    resp = get_from_candidate_resource(access_token=None, candidate_id=candidate_id)
    print response_info(resp)
    assert resp.status_code == 401
    assert resp.json()['error']['code'] == 11 # Bearer token not found


def test_get_candidate_without_id_or_email(sample_user, user_auth):
    """
    Test:   Attempt to retrieve candidate without providing ID or Email
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    resp = post_to_candidate_resource(token)
    print response_info(resp)
    assert resp.status_code == 201

    # Retrieve Candidate without providing ID or Email
    resp = request_to_candidates_resource(token, 'get')
    print response_info(resp)
    assert resp.status_code == 200
    assert len(resp.json()['candidates']) == 1


def test_get_candidate_from_forbidden_domain(sample_user, user_auth, user_from_different_domain):
    """
    Test:   Attempt to retrieve a candidate outside of logged-in-user's domain
    Expect: 403 status_code
    :type sample_user:      User
    :type sample_user_2:    User
    :type user_auth:        UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    resp = post_to_candidate_resource(token)
    resp_dict = resp.json()
    print response_info(resp)

    # Get access token for sample_user_2
    token_2 = user_auth.get_auth_token(user_from_different_domain, True)['access_token']

    # Retrieve candidate from a different domain
    candidate_id = resp_dict['candidates'][0]['id']
    resp = get_from_candidate_resource(access_token=token_2, candidate_id=candidate_id)
    print response_info(resp)
    assert resp.status_code == 403


def test_get_candidate_via_invalid_email(sample_user, user_auth):
    """
    Test:   Retrieve candidate via an invalid email address
    Expect: 400
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Retrieve Candidate via candidate's email
    resp = get_from_candidate_resource(access_token=token, candidate_email='bad_email.com')
    print response_info(resp)
    assert resp.status_code == 400


def test_get_can_via_id_and_email(sample_user, user_auth):
    """
    Test:   Retrieve candidate via candidate's ID and candidate's Email address
    Expect: 200 in both cases
    :type sample_user:    User
    :type user_auth:      UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate
    resp = post_to_candidate_resource(access_token=token, data=None, domain_id=sample_user.domain_id)
    resp_dict = resp.json()
    print response_info(resp)

    db.session.commit()

    # Candidate ID & Email
    candidate_id = resp_dict['candidates'][0]['id']
    candidate_email = db.session.query(Candidate).get(candidate_id).candidate_emails[0].address

    # Get candidate via Candidate ID
    resp = get_from_candidate_resource(access_token=token, candidate_id=candidate_id)

    resp_dict = resp.json()
    print response_info(resp)
    assert resp.status_code == 200
    assert isinstance(resp_dict, dict)
    assert check_for_id(_dict=resp_dict['candidate']) is not False

    # Get candidate via Candidate Email
    resp = get_from_candidate_resource(access_token=token, candidate_email=candidate_email)

    resp_dict = resp.json()
    print response_info(resp)
    assert resp.status_code == 200
    assert isinstance(resp_dict, dict)
    assert check_for_id(_dict=resp_dict['candidate']) is not False # assert every object has an id-key


def test_get_candidates_via_list_of_ids(sample_user, user_auth):
    """
    Test:   Retrieve candidates via a list of ids
    Expect: 200, list of Candidates
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidates
    can_id_1 = post_to_candidate_resource(token).json()['candidates'][0]['id']
    can_id_2 = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Get all candidates in user's domain
    data = {'candidate_ids': [can_id_1, can_id_2]}
    resp = request_to_candidates_resource(token, 'get', data)
    print response_info(resp)
    assert resp.status_code == 200
    assert len(resp.json()['candidates']) == 2