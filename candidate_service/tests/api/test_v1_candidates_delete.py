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
    request_to_candidate_education_degree_resource, request_to_candidate_education_degree_bullet_resource,
    request_to_candidate_experience_resource, request_to_candidate_experience_bullet_resource,
    request_to_candidate_work_preference_resource, request_to_candidate_email_resource,
    request_to_candidate_phone_resource, request_to_candidate_military_service,
    request_to_candidate_preferred_location_resource
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

######################## CandidateEducationDegreeBullet ########################
def test_delete_candidate_education_degree_bullets(sample_user, user_auth):
    """
    Test:   Remove all of candidate's degree_bullets from db
    Expect: 204; Candidate should not have any degrees left; Candidate's
    Education and degrees should not be removed
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

    # Current number of candidate educations & degrees
    count_of_educations_before_deleting = len(can_educations[0])
    count_of_edu_degrees_before_deleting = len(can_educations[0]['degrees'])

    # Remove all of Candidate's degree_bullets
    updated_resp = request_to_candidate_education_degree_bullet_resource(
        token, 'delete', candidate_id, can_educations[0]['id'], can_educations[0]['degrees'][0]['id'],
        True
    )
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == 0
    assert len(can_dict_after_update['educations'][0]) == count_of_educations_before_deleting
    assert len(can_dict_after_update['educations'][0]['degrees']) == count_of_edu_degrees_before_deleting


def test_delete_candidates_education_degree_bullet(sample_user, user_auth):
    """
    Test:   Remove Candidate's degree_bullet from db
    Expect: 204, Candidate's degree_bullet must be less 1. Candidate's education and degrees
            should not be removed
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
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations, degrees, and bullets
    educations_count_before_delete = len(candidate_educations)
    degrees_count_before_delete = len(candidate_educations[0]['degrees'])
    degree_bullets_count_before_delete = len(candidate_educations[0]['degrees'][0]['bullets'])

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_degree_bullet_resource(
        access_token=token, request='delete', candidate_id=candidate_id,
        education_id=candidate_educations[0]['id'],
        degree_id=candidate_educations[0]['degrees'][0]['id'],
        bullet_id=candidate_educations[0]['degrees'][0]['bullets'][0]['id']
    )
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == educations_count_before_delete
    assert len(can_dict_after_update['educations'][0]['degrees']) == degrees_count_before_delete
    assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == degree_bullets_count_before_delete - 1

######################## CandidateExperience ########################
def test_delete_candidate_experiences(sample_user, user_auth):
    """
    Test:   Remove all of candidate's experiences from db
    Expect: 204; Candidate should not have any experience left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    # Remove all of Candidate's experiences
    updated_resp = request_to_candidate_experience_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences']) == 0


def test_delete_candidates_experience(sample_user, user_auth):
    """
    Test:   Remove Candidate's experience from db
    Expect: 204, Candidate's experience must be less 1.
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
    candidate_experiences = candidate_dict['work_experiences']

    # Current number of Candidate's experiences
    experiences_count_before_delete = len(candidate_experiences)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_experience_resource(token, 'delete', candidate_id,
                                                            experience_id=candidate_experiences[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences']) == experiences_count_before_delete - 1

######################## CandidateExperienceBullet ########################
def test_delete_candidate_experience_bullets(sample_user, user_auth):
    """
    Test:   Remove all of Candidate's experience-bullets from db
    Expect: 204; Candidate should not have any experience bullets left.
            No experiences should be removed
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate Experiences
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_experiences = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_experiences']

    # Current Number of can_experiences
    experience_count_before_deleting_bullets = len(can_experiences)

    # Remove all of Candidate's experiences
    updated_resp = request_to_candidate_experience_bullet_resource(token, 'delete', candidate_id,
                                                                   can_experiences[0]['id'], True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences'][0]['bullets']) == 0
    assert len(can_dict_after_update['work_experiences']) == experience_count_before_deleting_bullets


def test_delete_candidates_experience_bullet(sample_user, user_auth):
    """
    Test:   Remove Candidate's experience-bullet from db
    Expect: 204, Candidate's experience-bullet must be less 1; no experiences must be removed
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate Experiences
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_experiences = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_experiences']

    # Current Number of can_experiences, and can_experiences' first bullets
    experience_count_before_deleting_bullets = len(can_experiences)
    experience_bullet_count_before_deleting = len(can_experiences[0]['bullets'])

    # Remove all of Candidate's experiences
    updated_resp = request_to_candidate_experience_bullet_resource(token, 'delete', candidate_id,
                                                                   can_experiences[0]['id'],
                                                                   bullet_id=can_experiences[0]['bullets'][0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences'][0]['bullets']) == experience_bullet_count_before_deleting - 1
    assert len(can_dict_after_update['work_experiences']) == experience_count_before_deleting_bullets

######################## CandidateEmail ########################
def test_delete_candidate_emails(sample_user, user_auth):
    """
    Test:   Remove Candidate's emails from db
    Expect: 204, Candidate must not have any emails left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete Candidate's work preference
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_email_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['emails']) == 0


def test_delete_candidate_email(sample_user, user_auth):
    """
    Test:   Remove Candidate's email from db
    Expect: 204, Candidate's emails must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's emails
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_emails = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']

    # Current number of candidate's emails
    emails_count_before_delete = len(can_emails)

    # Delete Candidate's work preference
    updated_resp = request_to_candidate_email_resource(token, 'delete', candidate_id,
                                                       email_id=can_emails[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate's emails after update
    can_emails_after_delete = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']

    assert updated_resp.status_code == 204
    assert len(can_emails_after_delete) == emails_count_before_delete - 1

######################## CandidateMilitaryService ########################
def test_delete_candidate_military_services(sample_user, user_auth):
    """
    Test:   Remove Candidate's military services from db
    Expect: 204, Candidate must not have any military services left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete Candidate's military services
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_military_service(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['military_services']) == 0


def test_delete_can_military_service(sample_user, user_auth):
    """
    Test:   Remove Candidate's military service from db
    Expect: 204, Candidate's military services must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's military services
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_military_services = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services']

    # Current number of candidate's military services
    military_services_count_before_delete = len(can_military_services)

    # Delete Candidate's military service
    updated_resp = request_to_candidate_military_service(token, 'delete', candidate_id,
                                                         military_service_id=can_military_services[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate's military services after update
    can_military_services_after_delete = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services']

    assert updated_resp.status_code == 204
    assert len(can_military_services_after_delete) == military_services_count_before_delete - 1

######################## CandidatePhone ########################
def test_delete_candidate_phones(sample_user, user_auth):
    """
    Test:   Remove Candidate's phones from db
    Expect: 204, Candidate must not have any phones left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete Candidate's phones
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_phone_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['phones']) == 0


def test_delete_candidate_phone(sample_user, user_auth):
    """
    Test:   Remove Candidate's phone from db
    Expect: 204, Candidate's phones must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's emails
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_phones = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones']

    # Current number of candidate's phones
    phones_count_before_delete = len(can_phones)

    # Delete Candidate's phone
    updated_resp = request_to_candidate_phone_resource(token, 'delete', candidate_id,
                                                       phone_id=can_phones[0]['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate's phones after update
    can_phones_after_delete = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones']

    assert updated_resp.status_code == 204
    assert len(can_phones_after_delete) == phones_count_before_delete - 1

######################## CandidatePreferredLocation ########################
def test_delete_candidate_preferred_locations(sample_user, user_auth):
    """
    Test:   Remove Candidate's preferred locations from db
    Expect: 204, Candidate must not have any preferred locations left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete Candidate's preferred locations
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_preferred_location_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['preferred_locations']) == 0


def test_delete_candidate_preferred_location(sample_user, user_auth):
    """
    Test:   Remove Candidate's preferred location from db
    Expect: 204, Candidate's preferred locations must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's preferred locations
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_preferred_locations = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations']

    # Current number of candidate's preferred locations
    preferred_locations_count_before_delete = len(can_preferred_locations)

    # Delete Candidate's preferred location
    updated_resp = request_to_candidate_preferred_location_resource(
        token, 'delete', candidate_id, preferred_location_id=can_preferred_locations[0]['id']
    )
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate's preferred locations after update
    can_preferred_locations_after_delete = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations']

    assert updated_resp.status_code == 204
    assert len(can_preferred_locations_after_delete) == preferred_locations_count_before_delete - 1


######################## CandidateWorkPreference ########################
def test_delete_candidate_work_preference(sample_user, user_auth):
    """
    Test:   Remove Candidate's work-preference from db
    Expect: 204, Candidate must not have any work-preference left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's work preference
    candidate_id = create_resp.json()['candidates'][0]['id']
    work_pref_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_preference']

    # Delete Candidate's work preference
    updated_resp = request_to_candidate_work_preference_resource(token, 'delete', candidate_id,
                                                                 work_pref_dict['id'])
    print response_info(updated_resp.request, resp_status=updated_resp.status_code)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_preference']) == 0

