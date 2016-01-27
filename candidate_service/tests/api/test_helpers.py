"""
Test cases for functions in helpers.py
"""
# Candidate Service app instance
from candidate_service.candidate_app import app
# Conftest
from candidate_service.common.tests.conftest import *
# Helper functions
from helpers import (
    request_to_candidate_resource, request_to_candidates_resource,
    check_for_id, remove_id_key, response_info, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data


def test_check_for_id(access_token_first, user_first, talent_pool):
    """
    Test:   Send candidate-dicts to check_for_id to ensure the function is behaving as expected
    Expect: False if candidate-dict has missing id-key(s)
    """
    # Create candidate
    AddUserRoles.add_and_get(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    resp = request_to_candidates_resource(access_token_first, 'post', data)
    candidate_id = resp.json()['candidates'][0]['id']

    candidate_dict = request_to_candidate_resource(
            access_token_first, 'get', candidate_id).json()['candidate']

    r = check_for_id(_dict=candidate_dict)
    assert r is None

    # Send candidate-dict with an empty dict, e.g. work_preference = {}
    _dict = candidate_dict.copy()
    _dict['work_preference'] = {}
    r = check_for_id(_dict=_dict)
    assert r is None

    # Remove top-level id-key
    _dict = candidate_dict.copy()
    del _dict['id']
    r = check_for_id(_dict=_dict)
    assert r is False

    # Remove id-key of the first address-dict in addresses
    _dict = candidate_dict.copy()
    del _dict['addresses'][0]['id']
    r = check_for_id(_dict=_dict)
    assert r is False

    # Remove id-key from first education-dict in educations
    _dict = candidate_dict.copy()
    del _dict['educations'][0]['id']
    r = check_for_id(_dict=_dict)
    assert r is False

    # Remove id-key from first degree-dict in educations
    _dict = candidate_dict.copy()
    del _dict['educations'][0]['degrees'][0]['id']
    r = check_for_id(_dict=_dict)
    assert r is False

    # Remove id-key from first degree_bullet-dict in degrees
    _dict = candidate_dict.copy()
    del _dict['educations'][0]['degrees'][0]['bullets'][0]['id']
    r = check_for_id(_dict=_dict)
    assert r is False

    # Remove id-key from work_preference
    _dict = candidate_dict.copy()
    del _dict['work_preference']['id']
    r = check_for_id(_dict=_dict)
    assert r is False


def test_remove_id_key(access_token_first, user_first, talent_pool):
    """
    Test:   Send candidate-dict with IDs to remove_id_key() to help remove all the id-keys
            from candidate-dict
    Expect: Candidate dict with no id-key
    """
    # Create Candidate
    AddUserRoles.add_and_get(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    get_resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    candidate_dict_with_ids = get_resp.json()['candidate']
    print response_info(get_resp)

    # Send Candidate dict with IDs to remove_id_keys
    candidate_dict_without_ids = remove_id_key(_dict=candidate_dict_with_ids.copy())
    print "candidate_dict_without_ids = %s" % candidate_dict_without_ids