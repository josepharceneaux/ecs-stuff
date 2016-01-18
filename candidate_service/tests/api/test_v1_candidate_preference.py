"""
Test cases for CandidatePreferenceResource
"""
# Standard library
import json

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
    request_to_candidate_preference_resource, AddUserRoles
)
from candidate_service.common.utils.handy_functions import add_role_to_test_user


#####################
# Test cases for POST
#####################
def test_add_subs_preference_to_candidate_without_providing_any_data(sample_user, user_auth):
    """
    Test:  Add subscription preference to candidate without sending any data,
           Or sending an empty data, i.e. {}
    Expect:  400
    :type sample_user:  User
    :type user_auth:  UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.add(user=sample_user)

    # Create candidate and candidate subscription preference
    create_resp = post_to_candidate_resource(token)
    candidate_id = create_resp.json()['candidates'][0]['id']
    create_subs_pref = request_to_candidate_preference_resource(token, 'post', candidate_id)
    print response_info(create_subs_pref)
    assert create_subs_pref.status_code == 400
    assert create_subs_pref.json()['error']['code'] == 3000
    create_subs_pref = request_to_candidate_preference_resource(token, 'post', candidate_id, {})
    print response_info(create_subs_pref)
    assert create_subs_pref.status_code == 400
    assert create_subs_pref.json()['error']['code'] == 3000


def test_add_candidate_subs_preference(sample_user, user_auth):
    """
    Test: Add subscription preference for the candidate
    Expect: 204
    :type sample_user: User
    :type user_auth:   UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.add_and_get(user=sample_user)

    # Create candidate and candidate subscription preference
    candidate_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    data = {'frequency_id': 1}
    resp = request_to_candidate_preference_resource(token, 'post', candidate_id, data)
    print response_info(resp)
    assert resp.status_code == 204

    # Retrieve Candidate's subscription preference
    resp = request_to_candidate_preference_resource(token, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 200
    assert resp.json()['candidate']['subscription_preference']['frequency_id'] == 1


####################
# Test cases for GET
####################
def test_get_non_existing_candidate_preference(sample_user, user_auth):
    """
    Test: Retrieve candidate's preferences that don't exist in the database
    Expect:  404
    :type sample_user:  User
    :type user_auth:  UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.add_and_get(user=sample_user)

    # Create candidate
    create_resp = post_to_candidate_resource(token)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # Retrieve subscription preference of the candidate
    resp = request_to_candidate_preference_resource(token, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 404
    assert resp.json()['error']['code'] == 3142


####################
# Test cases for PUT
####################
def test_update_non_existing_candidate_preference(sample_user, user_auth):
    """
    Test: Attempt to update a non existing candidate subs preference
    Expect: 400, although it's "not found" it is however a misuse of the resource
    :type sample_user:  User
    :type user_auth:   UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.add_get_update(user=sample_user)

    # Create candidate
    create_resp = post_to_candidate_resource(token)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # Update candidate's subscription preferences
    data = {'frequency_id': 1} # this is arbitrary
    resp = request_to_candidate_preference_resource(token, 'put', candidate_id, data)
    print response_info(resp)
    assert resp.status_code == 400
    assert resp.json()['error']['code'] == 3142


def test_update_candidate_pref_without_providing_adequate_data(sample_user, user_auth):
    """
    Test: Attempt to update candidate's subs pref with missing data
    Expect: 400
    :type sample_user:  User
    :type user_auth:  UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.add_get_update(user=sample_user)

    # Create candidate
    candidate_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Update candidate's subs preference with missing inputs
    data_1, data_2, data_3, data_4 = None, {}, {'': ''}, {'frequency_id': None}
    resp_1 = request_to_candidate_preference_resource(token, 'put', candidate_id, data_1)
    resp_2 = request_to_candidate_preference_resource(token, 'put', candidate_id, data_2)
    resp_3 = request_to_candidate_preference_resource(token, 'put', candidate_id, data_3)
    resp_4 = request_to_candidate_preference_resource(token, 'put', candidate_id, data_4)
    print response_info(resp_1), response_info(resp_2), response_info(resp_3), response_info(resp_4)
    assert resp_1.status_code == 400 and resp_1.json()['error']['code'] == 3000
    assert resp_2.status_code == 400 and resp_2.json()['error']['code'] == 3000
    assert resp_3.status_code == 400 and resp_3.json()['error']['code'] == 3000
    assert resp_4.status_code == 400 and resp_4.json()['error']['code'] == 3000


def test_update_subs_pref_of_a_non_existing_candidate(sample_user, user_auth):
    """
    Test: Attempt to update the subs pref of a non existing candidate
    Expect: 404
    :type sample_user: User
    :type user_auth:   UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.edit(user=sample_user)

    # Update candidate's subs preference
    last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
    non_existing_candidate_id = last_candidate.id * 100
    data = {'frequency_id': 1}
    resp = request_to_candidate_preference_resource(token, 'put', non_existing_candidate_id, data)
    print response_info(resp)
    assert resp.status_code == 404 and resp.json()['error']['code'] == 3010


def test_update_subs_pref_of_candidate(sample_user, user_auth):
    """
    Test: Update candidate's subscription preference
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.all_roles(user=sample_user)

    # Create candidate and candidate's subscription preference
    candidate_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    request_to_candidate_preference_resource(token, 'post', candidate_id, {'frequency_id': 1})

    # Update candidate's subscription preference
    resp = request_to_candidate_preference_resource(token, 'put', candidate_id, {'frequency_id': 2})
    assert resp.status_code == 204

    # Retrieve candidate's subscription preference
    resp = request_to_candidate_preference_resource(token, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 200
    assert resp.json()['candidate']['id'] == candidate_id
    assert resp.json()['candidate']['subscription_preference']['frequency_id'] == 2

#######################
# Test cases for DELETE
#######################
def test_delete_candidate_preference(sample_user, user_auth):
    """
    Test: Delete candidate's subscription preference
    Expect: 204
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.all_roles(user=sample_user)

    # Create candidate and candidate's subscription preference
    candidate_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    request_to_candidate_preference_resource(token, 'post', candidate_id, {'frequency_id': 1})

    # Update candidate's subscription preference
    resp = request_to_candidate_preference_resource(token, 'delete', candidate_id)
    print response_info(resp)
    assert resp.status_code == 204

    # Retrieve candidate's subscription preference
    resp = request_to_candidate_preference_resource(token, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 404 and resp.json()['error']['code'] == 3142