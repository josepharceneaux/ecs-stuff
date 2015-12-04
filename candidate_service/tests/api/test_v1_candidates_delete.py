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
    request_to_candidate_resource, request_to_candidate_address_resource,
    request_to_candidate_aoi_resource, request_to_candidate_education_resource,
    request_to_candidate_education_degree_resource
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
    resp = request_to_candidate_resource(token, 'delete', candidate_id)
    print response_info(resp.request, resp.json(), resp.status_code)

    # Retrieve Candidate
    get_resp = get_from_candidate_resource(token, candidate_id)
    print response_info(get_resp.request, get_resp.json(), get_resp.status_code)

    assert get_resp.status_code == 404


######################## CandidateAddress ########################
def test_delete_candidate_address(sample_user, user_auth):
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
    updated_resp = request_to_candidate_address_resource(token, 'delete', candidate_id,
                                                         address_id=candidate_addresses[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['addresses']) == candidate_addresses_count - 1


def test_delete_all_of_candidates_addresses(sample_user, user_auth):
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
    updated_resp = request_to_candidate_address_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['addresses']) == 0

######################## CandidateAreaOfInterest ########################
def test_delete_all_of_candidates_areas_of_interest(sample_user, user_auth):
    """
    Test:   Remove all of candidate's aois from db
    Expect: 204, Candidate should not have any aois left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate's aois
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_aois = get_from_candidate_resource(token, candidate_id).json()['candidate']['areas_of_interest']

    # Remove all of Candidate's areas of interest
    updated_resp = request_to_candidate_aoi_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['areas_of_interest']) == 0
    assert db.session.query(AreaOfInterest).get(can_aois[0]['id']) # AreaOfInterest should still be in db
    assert db.session.query(AreaOfInterest).get(can_aois[1]['id']) # AreaOfInterest should still be in db


def test_delete_candidate_aoi(sample_user, user_auth):
    """
    Test:   Remove Candidate's area_of_interest from db
    Expect: 204, Candidate's aois must be less 1 AND no AreaOfInterest should be deleted
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_aois = candidate_dict['areas_of_interest']

    # Number of Candidate's aois
    candidate_aois_count = len(candidate_aois)

    # Remove one of Candidate's aois
    updated_resp = request_to_candidate_aoi_resource(token, 'delete', candidate_id, aoi_id=candidate_aois[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['areas_of_interest']) == candidate_aois_count - 1
    assert db.session.query(AreaOfInterest).get(candidate_aois[0]['id']) # AreaOfInterest should still be in db
    assert db.session.query(AreaOfInterest).get(candidate_aois[1]['id']) # AreaOfInterest should still be in db

######################## CandidateEducation ########################
def test_delete_candidate_educations(sample_user, user_auth):
    """
    Test:   Remove all of candidate's educations from db
    Expect: 204, Candidate should not have any educations left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Remove all of Candidate's educations
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == 0


def test_delete_candidates_education(sample_user, user_auth):
    """
    Test:   Remove Candidate's education from db
    Expect: 204, Candidate's education must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations
    candidate_educations_count = len(candidate_educations)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id,
                                                           education_id=candidate_educations[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == candidate_educations_count - 1

######################## CandidateEducationDegree ########################
def test_delete_candidate_education_degrees(sample_user, user_auth):
    """
    Test:   Remove all of candidate's degrees from db
    Expect: 204; Candidate should not have any degrees left; Candidate's Education should not be removed
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_educations = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations']

    # Current number of candidate educations
    count_of_edu_degrees_before_deleting = len(can_educations[0])

    # Remove all of Candidate's degrees
    updated_resp = request_to_candidate_education_degree_resource(token, 'delete', candidate_id,
                                                                  can_educations[0]['id'], True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations'][0]['degrees']) == 0
    assert len(can_dict_after_update['educations'][0]) == count_of_edu_degrees_before_deleting


def test_delete_candidates_education_degree(sample_user, user_auth):
    """
    Test:   Remove Candidate's education from db
    Expect: 204, Candidate's education must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations
    candidate_educations_count = len(candidate_educations)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id,
                                                           education_id=candidate_educations[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == candidate_educations_count - 1