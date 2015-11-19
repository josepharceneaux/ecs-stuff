"""
Test cases for functions in helpers.py
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
    check_for_id, post_to_candidate_resource, get_from_candidate_resource
)


def test_check_for_id(sample_user, user_auth):
    """
    Test:   Send candidate-dicts to check_for_id to ensure the function is behaving as expected
    Expect: False if candidate-dict has missing id-key(s)
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate
    resp = post_to_candidate_resource(token)
    candidate_id = resp.json()['candidates'][0]['id']

    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    r = check_for_id(candidate_dict=candidate_dict)
    assert r is None

    # Send candidate-dict with an empty dict, e.g. work_preference = {}
    _dict = candidate_dict.copy()
    _dict['work_preference'] = {}
    r = check_for_id(candidate_dict=_dict)
    assert r is None

    # Remove top-level id-key
    _dict = candidate_dict.copy()
    del _dict['id']
    r = check_for_id(candidate_dict=_dict)
    assert r is False

    # Remove id-key of the first address-dict in addresses
    _dict = candidate_dict.copy()
    del _dict['addresses'][0]['id']
    r = check_for_id(candidate_dict=_dict)
    assert r is False

    # Remove id-key from first education-dict in educations
    _dict = candidate_dict.copy()
    del _dict['educations'][0]['id']
    r = check_for_id(candidate_dict=_dict)
    assert r is False

    # Remove id-key from first degree-dict in educations
    _dict = candidate_dict.copy()
    del _dict['educations'][0]['degrees'][0]['id']
    r = check_for_id(candidate_dict=_dict)
    assert r is False

    # Remove id-key from first degree_bullet-dict in degrees
    _dict = candidate_dict.copy()
    del _dict['educations'][0]['degrees'][0]['degree_bullets'][0]['id']
    r = check_for_id(candidate_dict=_dict)
    assert r is False

    # Remove id-key from work_preference
    _dict = candidate_dict.copy()
    del _dict['work_preference']['id']
    r = check_for_id(candidate_dict=_dict)
    assert r is False
