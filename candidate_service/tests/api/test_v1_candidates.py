"""
Test cases for candidate-restful-services
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
    update_candidate, create_same_candidate
)

####################################
# test cases for GETting candidate #
####################################
def test_get_candidate_without_authed_user(sample_user, user_auth):
    """
    Test:   attempt to retrieve candidate with bad access_token
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201

    # Retrieve Candidate
    candidate_id = resp_dict['candidates'][0]['id']
    resp = get_from_candidate_resource(access_token=None, candidate_id=candidate_id)

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 401
    assert 'error' in resp_dict


def test_get_candidate_without_id_or_email(sample_user, user_auth):
    """
    Test:   attempt to retrieve candidate without providing ID or Email
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201

    # Retrieve Candidate without providing ID or Email
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'])

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp_dict


def test_get_candidate_from_forbidden_domain(sample_user, user_auth, sample_user_2):
    """
    Test:   attempt to retrieve a candidate outside of logged-in-user's domain
    Expect: 403 status_code

    :type sample_user:      User
    :type sample_user_2:    User
    :type user_auth:        UserAuthentication
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]

    # Get auth token for sample_user_2
    auth_token_row = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)

    # Retrieve candidate from a different domain
    candidate_id = resp_dict['candidates'][0]['id']
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_id=candidate_id)

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 403
    assert 'error' in resp_dict


def test_get_candidate_via_invalid_email(sample_user, user_auth):
    """
    Test:   retrieve candidate via an invalid email address
    Expect: 400
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Retrieve candidate via candidate's email
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_email='bad_email.com')

    print response_info(resp.request, resp.json(), resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp.json()


def test_get_candidate_via_id_and_email(sample_user, user_auth):
    """
    Test:   retrieve candidate via candidate's ID and candidate's Email address
    Expect: 200 in both cases
    :type sample_user:    User
    :type user_auth:      UserAuthentication
    """
    # Get auth token
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)

    db.session.commit()

    # Candidate ID & Email
    candidate_id = resp_dict['candidates'][0]['id']
    candidate_email = db.session.query(Candidate).get(candidate_id).candidate_emails[0].address

    # Get candidate via Candidate ID
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_id=candidate_id)

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 200
    assert 'candidate' in resp_dict and 'id' in resp_dict['candidate']

    # Get candidate via Candidate Email
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_email=candidate_email)

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 200
    assert 'candidate' in resp_dict and 'id' in resp_dict['candidate']

#######################################
# test cases for POSTing candidate(s) #
#######################################
def test_create_candidate(sample_user, user_auth):
    """
    Test:   create a new candidate and candidate's info
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


def test_create_an_existing_candidate(sample_user, user_auth):
    """
    Test:   attempt to create (recreate?) an existing Candidate
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create same Candidate twice
    resp = create_same_candidate(access_token=auth_token_row['access_token'])

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp_dict

########################################
# test cases for PATCHing candidate(s) #
########################################
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



