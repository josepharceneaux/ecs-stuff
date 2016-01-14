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
    request_to_candidate_preference_resource
)

# Sample data
from candidate_sample_data import (
    generate_single_candidate_data, candidate_educations, candidate_experience,
    candidate_work_preference, candidate_phones, candidate_military_service,
    candidate_preferred_locations, candidate_skills, candidate_social_network,
    candidate_areas_of_interest, candidate_custom_fields, reset_all_data_except_param,
    complete_candidate_data_for_posting
)
from candidate_service.common.utils.handy_functions import add_role_to_test_user


def test_add_subs_preference_to_candidate_without_any_data(sample_user, user_auth):
    """
    Test:  Add subscription preference to candidate without sending any data,
           Or sending an empty data, i.e. {}
    Expect:  400
    :type sample_user:  User
    :type user_auth:  UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    add_role_to_test_user(sample_user, ['CAN_ADD_PREFERENCES'])

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


def test_get_non_existing_candidate_preference(sample_user, user_auth):
    """
    Test: Retrieve candidate's preferences that don't exist in the database
    Expect:  404
    :type sample_user:  User
    :type user_auth:  UserAuthentication
    """
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    add_role_to_test_user(sample_user, ['CAN_GET_PREFERENCES'])

    # Create candidate
    create_resp = post_to_candidate_resource(token)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # Retrieve subscription preference of the candidate
    resp = request_to_candidate_preference_resource(token, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 404
    assert resp.json()['error']['code'] == 3142


