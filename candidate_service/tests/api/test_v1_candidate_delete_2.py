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
    request_to_candidate_experience_resource, request_to_candidate_experience_bullet_resource,
    request_to_candidate_work_preference_resource, request_to_candidate_email_resource,
    request_to_candidate_phone_resource, request_to_candidate_military_service,
    request_to_candidate_preferred_location_resource, request_to_candidate_skill_resource,
    request_to_candidate_social_network_resource
)


######################## CandidateExperience ########################
def test_non_logged_in_user_delete_can_experience():
    """
    Test:   Delete candidate's experiences without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's experiences
    resp = request_to_candidate_experience_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_experience_with_bad_input():
    """
    Test:   Attempt to delete candidate experience with non integer values for candidate_id & experience_id
    Expect: 404
    """
    # Delete Candidate's experiences
    resp = request_to_candidate_experience_resource(None, 'delete', candidate_id='x', all_experiences=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's experience
    resp = request_to_candidate_experience_resource(None, 'delete', candidate_id=5, experience_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_experience_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the experience of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's experience with sample_user_2 logged in
    updated_resp = request_to_candidate_experience_resource(token_2, 'delete',
                                                            candidate_1_id, all_experiences=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_experience_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the experience of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's experiences
    can_2_experiences = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['work_experiences']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_experience_resource(token, 'delete', candidate_1_id,
                                                         experience_id=can_2_experiences[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_experience_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's experience without providing experience_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's experiences without experience_id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_experience_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_experiences_without_can_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's experiences without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's experiences without candidate_id
    updated_resp = request_to_candidate_experience_resource(token, 'delete', all_experiences=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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
    candidate_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Remove all of Candidate's experiences
    updated_resp = request_to_candidate_experience_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences']) == 0


def test_delete_candidate_experience(sample_user, user_auth):
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
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences']) == experiences_count_before_delete - 1


######################## CandidateExperienceBullet ########################
def test_non_logged_in_user_delete_can_experience_bullets():
    """
    Test:   Delete candidate's experience-bullets without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's experience-bullets
    resp = request_to_candidate_experience_bullet_resource(None, 'delete', 5, 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_experience_bullet_with_bad_input():
    """
    Test:   Attempt to delete candidate experience-bullet with non integer values
            for candidate_id & experience_id
    Expect: 404
    """
    # Delete Candidate's experience-bullets
    resp = request_to_candidate_experience_bullet_resource(None, 'delete', candidate_id='x',
                                                           experience_id=5, all_bullets=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's experience-bullet
    resp = request_to_candidate_experience_bullet_resource(None, 'delete', candidate_id=5,
                                                           experience_id=5, bullet_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_exp_bullets_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete exp-bullets of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1's experiences
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']
    experience = get_from_candidate_resource(token_1, candidate_1_id).json()['candidate']['work_experiences'][0]

    # Delete candidate_1's exp-bullets with sample_user_2 logged in
    updated_resp = request_to_candidate_experience_bullet_resource(token_2, 'delete', candidate_1_id,
                                                                   experience_id=experience['id'],
                                                                   all_bullets=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_exp_bullets_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the exp-bullets of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's experiences
    can_2_experiences = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['work_experiences']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_experience_bullet_resource(token, 'delete', candidate_1_id,
                                                                   experience_id=can_2_experiences[0]['id'],
                                                                   all_bullets=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_exp_bullets_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's exp-bullets without providing bullet_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's exp-bullets without an id
    candidate_id, experience_id = 5, 5 # These are arbitrary since a 404 is expected
    updated_resp = request_to_candidate_experience_bullet_resource(token, 'delete', candidate_id, experience_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_exp_bullets_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's exp-bullets without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's exp-bullets without candidate_id
    updated_resp = request_to_candidate_experience_bullet_resource(token, 'delete', experience_id=5, bullet_id=5)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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
    print response_info(updated_resp)

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
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_experiences'][0]['bullets']) == experience_bullet_count_before_deleting - 1
    assert len(can_dict_after_update['work_experiences']) == experience_count_before_deleting_bullets


######################## CandidateEmail ########################
def test_non_logged_in_user_delete_can_emails():
    """
    Test:   Delete candidate's emails without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's emails
    resp = request_to_candidate_email_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_email_with_bad_input():
    """
    Test:   Attempt to delete candidate email with non integer values for candidate_id & email_id
    Expect: 404
    """
    # Delete Candidate's emails
    resp = request_to_candidate_email_resource(None, 'delete', candidate_id='x', all_emails=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's email
    resp = request_to_candidate_email_resource(None, 'delete', candidate_id=5, email_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_email_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the email of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's email with sample_user_2 logged in
    updated_resp = request_to_candidate_email_resource(token_2, 'delete', candidate_1_id, all_emails=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_email_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the email of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's emails
    can_2_emails = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['emails']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_email_resource(token, 'delete', candidate_1_id,
                                                         email_id=can_2_emails[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_email_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's email without providing email_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's emails without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_email_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_emails_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's email without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's emails without candidate_id
    updated_resp = request_to_candidate_email_resource(token, 'delete', all_emails=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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

    # Delete Candidate's emails
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_email_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

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

    # Delete Candidate's email
    updated_resp = request_to_candidate_email_resource(token, 'delete', candidate_id,
                                                       email_id=can_emails[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate's emails after update
    can_emails_after_delete = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']

    assert updated_resp.status_code == 204
    assert len(can_emails_after_delete) == emails_count_before_delete - 1


######################## CandidateMilitaryService ########################
def test_non_logged_in_user_delete_can_military_service():
    """
    Test:   Delete candidate's military_services without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's military_services
    resp = request_to_candidate_military_service(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_military_service_with_bad_input():
    """
    Test:   Attempt to delete candidate military_services with non integer values
            for candidate_id & military_service_id
    Expect: 404
    """
    # Delete Candidate's military_services
    resp = request_to_candidate_military_service(None, 'delete', candidate_id='x', all_military_services=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's military_service
    resp = request_to_candidate_military_service(None, 'delete', candidate_id=5, military_service_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_military_service_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the military_services of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's military_services with sample_user_2 logged in
    updated_resp = request_to_candidate_military_service(token_2, 'delete', candidate_1_id,
                                                         all_military_services=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_military_service_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the military_service of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's military_services
    can_2_military_services = get_from_candidate_resource(token, candidate_2_id).\
        json()['candidate']['military_services']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_military_service(token, 'delete', candidate_1_id,
                                                         military_service_id=can_2_military_services[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_military_service_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's military_service without providing military_service_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's military_services without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_military_service(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_military_services_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's military_services without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's military_services without candidate_id
    updated_resp = request_to_candidate_military_service(token, 'delete', all_military_services=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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
    print response_info(updated_resp)

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
    print response_info(updated_resp)

    # Retrieve Candidate's military services after update
    can_military_services_after_delete = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services']

    assert updated_resp.status_code == 204
    assert len(can_military_services_after_delete) == military_services_count_before_delete - 1


######################## CandidatePhone ########################
def test_non_logged_in_user_delete_can_phone():
    """
    Test:   Delete candidate's phone without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's phones
    resp = request_to_candidate_phone_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_phone_with_bad_input():
    """
    Test:   Attempt to delete candidate phone with non integer values for candidate_id & phone_id
    Expect: 404
    """
    # Delete Candidate's phones
    resp = request_to_candidate_phone_resource(None, 'delete', candidate_id='x', all_phones=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's phone
    resp = request_to_candidate_phone_resource(None, 'delete', candidate_id=5, phone_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_phone_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the phone of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's phone with sample_user_2 logged in
    updated_resp = request_to_candidate_phone_resource(token_2, 'delete', candidate_1_id, all_phones=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_phone_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the phone of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's phones
    can_2_phonees = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['phones']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_phone_resource(token, 'delete', candidate_1_id,
                                                         phone_id=can_2_phonees[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_phone_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's phone without providing phone_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's phones without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_phone_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_phones_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's phone without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's phones without an id
    updated_resp = request_to_candidate_phone_resource(token, 'delete', all_phones=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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
    print response_info(updated_resp)

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

    # Retrieve Candidate's phones
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_phones = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones']

    # Current number of candidate's phones
    phones_count_before_delete = len(can_phones)

    # Delete Candidate's phone
    updated_resp = request_to_candidate_phone_resource(token, 'delete', candidate_id,
                                                       phone_id=can_phones[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate's phones after update
    can_phones_after_delete = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones']

    assert updated_resp.status_code == 204
    assert len(can_phones_after_delete) == phones_count_before_delete - 1


######################## CandidatePreferredLocation ########################
def test_non_logged_in_user_delete_can_preferred_location():
    """
    Test:   Delete candidate's preferred location without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's preferred locations
    resp = request_to_candidate_preferred_location_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_preferred_location_with_bad_input():
    """
    Test:   Attempt to delete candidate preferred location with non integer values
            for candidate_id & preferred_location_id
    Expect: 404
    """
    # Delete Candidate's preferred locations
    resp = request_to_candidate_preferred_location_resource(None, 'delete', candidate_id='x',
                                                            all_preferred_locations=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's preferred location
    resp = request_to_candidate_preferred_location_resource(None, 'delete', candidate_id=5,
                                                            preferred_location_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_preferred_location_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete preferred locations of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's preferred locations with sample_user_2 logged in
    updated_resp = request_to_candidate_preferred_location_resource(token_2, 'delete', candidate_1_id,
                                                                    all_preferred_locations=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_preferred_location_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the preferred location of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's preferred locations
    can_2_preferred_locationes = get_from_candidate_resource(token, candidate_2_id).\
        json()['candidate']['preferred_locations']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_preferred_location_resource(token, 'delete', candidate_1_id,
                                                         preferred_location_id=can_2_preferred_locationes[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_preferred_location_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's preferred location without providing preferred_location_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's preferred location without preferred location ID
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_preferred_location_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_preferred_locations_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's preferred locations without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's preferred locations without an id
    updated_resp = request_to_candidate_preferred_location_resource(token, 'delete', all_preferred_locations=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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
    print response_info(updated_resp)

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
    print response_info(updated_resp)

    # Retrieve Candidate's preferred locations after update
    can_preferred_locations_after_delete = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations']

    assert updated_resp.status_code == 204
    assert len(can_preferred_locations_after_delete) == preferred_locations_count_before_delete - 1


######################## CandidateSkill ########################
def test_non_logged_in_user_delete_can_skill():
    """
    Test:   Delete candidate's skills without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's skills
    resp = request_to_candidate_skill_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_skill_with_bad_input():
    """
    Test:   Attempt to delete candidate skill with non integer values for candidate_id & skill_id
    Expect: 404
    """
    # Delete Candidate's skills
    resp = request_to_candidate_skill_resource(None, 'delete', candidate_id='x', all_skills=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's skill
    resp = request_to_candidate_skill_resource(None, 'delete', candidate_id=5, skill_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_skill_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the skill of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's skills with sample_user_2 logged in
    updated_resp = request_to_candidate_skill_resource(token_2, 'delete', candidate_1_id, all_skills=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_skill_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete skill of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's skills
    can_2_skills = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['skills']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_skill_resource(token, 'delete', candidate_1_id,
                                                         skill_id=can_2_skills[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_skill_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's skill without providing skill_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's skills without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_skill_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_skills_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's skills without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's skills without candidate_id
    updated_resp = request_to_candidate_skill_resource(token, 'delete', all_skills=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_skills(sample_user, user_auth):
    """
    Test:   Remove Candidate's skills from db
    Expect: 204, Candidate must not have any skills left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete Candidate's skills
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_skill_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['skills']) == 0


def test_delete_cand_skill(sample_user, user_auth):
    """
    Test:   Remove Candidate's skill from db
    Expect: 204, Candidate's skills must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's skills
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_skills = get_from_candidate_resource(token, candidate_id).json()['candidate']['skills']

    # Current number of candidate's phones
    skills_count_before_delete = len(can_skills)

    # Delete Candidate's skill
    updated_resp = request_to_candidate_skill_resource(token, 'delete', candidate_id,
                                                       skill_id=can_skills[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate's skills after update
    can_skills_after_delete = get_from_candidate_resource(token, candidate_id).json()['candidate']['skills']

    assert updated_resp.status_code == 204
    assert len(can_skills_after_delete) == skills_count_before_delete - 1


######################## CandidateSocialNetwork ########################
def test_non_logged_in_user_delete_can_social_network():
    """
    Test:   Delete candidate's social nerwork without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's social networks
    resp = request_to_candidate_social_network_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_social_network_with_bad_input():
    """
    Test:   Attempt to delete candidate social network with non integer values
            for candidate_id & social_network_id
    Expect: 404
    """
    # Delete Candidate's social networks
    resp = request_to_candidate_social_network_resource(None, 'delete', candidate_id='x', all_sn=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's social network
    resp = request_to_candidate_social_network_resource(None, 'delete', candidate_id=5, sn_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_social_network_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the social networks of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's social networks with sample_user_2 logged in
    updated_resp = request_to_candidate_social_network_resource(token_2, 'delete', candidate_1_id, all_sn=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_social_network_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the social network of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's social networks
    can_2_social_networkes = get_from_candidate_resource(token, candidate_2_id).\
        json()['candidate']['social_networks']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_social_network_resource(token, 'delete', candidate_1_id,
                                                         sn_id=can_2_social_networkes[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_social_network_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's social network without providing social_network_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's social network without social network ID
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_social_network_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_social_networks_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's social network without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's social networks without candidate ID
    updated_resp = request_to_candidate_social_network_resource(token, 'delete', all_sn=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_social_networks(sample_user, user_auth):
    """
    Test:   Remove Candidate's social networks from db
    Expect: 204, Candidate must not have any social networks left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete Candidate's social networks
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_social_network_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['social_networks']) == 0


def test_delete_can_social_network(sample_user, user_auth):
    """
    Test:   Remove Candidate's social network from db
    Expect: 204, Candidate's social networks must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate's social networks
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_sn = get_from_candidate_resource(token, candidate_id).json()['candidate']['social_networks']

    # Current number of candidate's social networks
    sn_count_before_delete = len(can_sn)

    # Delete Candidate's skill
    updated_resp = request_to_candidate_social_network_resource(token, 'delete',
                                                                candidate_id, sn_id=can_sn[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate's social networks after update
    can_sn_after_delete = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['social_networks']

    assert updated_resp.status_code == 204
    assert len(can_sn_after_delete) == sn_count_before_delete - 1


######################## CandidateWorkPreference ########################
def test_non_logged_in_user_delete_can_work_preference():
    """
    Test:   Delete candidate's work preference without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's work preference
    candidate_id, work_preference_id = 5, 5 # These are arbitrary since a 401 is expected
    resp = request_to_candidate_work_preference_resource(None, 'delete', candidate_id, work_preference_id)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_work_preference_with_bad_input():
    """
    Test:   Attempt to delete candidate work preference with non integer values
            for candidate_id & work_preference_id
    Expect: 404
    """
    # Delete Candidate's work preference
    resp = request_to_candidate_work_preference_resource(None, 'delete', candidate_id='x', work_preference_id=5)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's work preference
    resp = request_to_candidate_work_preference_resource(None, 'delete', candidate_id=5, work_preference_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_work_preference_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the work preference of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1's work preference
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']
    can_1_work_preference = get_from_candidate_resource(token_1, candidate_1_id).\
        json()['candidate']['work_preference']

    # Delete candidate_1's work preference with sample_user_2 logged in
    updated_resp = request_to_candidate_work_preference_resource(token_2, 'delete', candidate_1_id,
                                                                 can_1_work_preference['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_work_preference_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the work preference of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's work preference
    can_2_work_preference = get_from_candidate_resource(token, candidate_2_id).\
        json()['candidate']['work_preference']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_work_preference_resource(token, 'delete', candidate_1_id,
                                                         work_preference_id=can_2_work_preference['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_work_preference_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's work preference without providing work_preference_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's work preference without work preference ID
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_work_preference_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_work_preferences_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's work preference without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's work preference without candidate ID
    updated_resp = request_to_candidate_work_preference_resource(token, 'delete')
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


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
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['work_preference']) == 0

