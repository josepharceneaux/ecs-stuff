"""
Test cases for CandidateResource/patch()
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
    patch_to_candidate_resource
)
from candidate_service.common.utils.handy_functions import add_role_to_test_user

# Candidate sample data
from candidate_sample_data import (
    fake, generate_single_candidate_data, candidate_data_for_update, candidate_addresses,
    candidate_areas_of_interest, candidate_educations, candidate_experience,
    candidate_work_preference, candidate_emails, candidate_phones, candidate_custom_fields
)


######################## Candidate ########################
def test_update_candidate_outside_of_domain(sample_user, user_auth, user_from_different_domain):
    """
    Test: User attempts to update a candidate from a different domain
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    :type user_from_different_domain:  User
    """
    # Get access tokens
    sample_user_token = user_auth.get_auth_token(sample_user, True)['access_token']
    user_from_other_domain_token = user_auth.\
        get_auth_token(user_from_different_domain, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(sample_user_token)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # User from different domain to update candidate
    data = {'candidates': [{'id': candidate_id, 'first_name': 'moron'}]}
    update_resp = patch_to_candidate_resource(user_from_other_domain_token, data)
    print response_info(update_resp)
    assert update_resp.status_code == 403


def test_update_existing_candidate(sample_user, user_auth):
    """
    Test:   Update an existing Candidate
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create a candidate
    create_candidate = post_to_candidate_resource(token).json()

    # Retrieve Candidate
    candidate_id = create_candidate['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    data = candidate_data_for_update(
            candidate_id=candidate_id,
            email_1_id=candidate_dict['emails'][0]['id'],
            email_2_id=candidate_dict['emails'][1]['id'],
            phone_1_id=candidate_dict['phones'][0]['id'],
            phone_2_id=candidate_dict['phones'][1]['id'],
            address_1_id=candidate_dict['addresses'][0]['id'],
            address_2_id=candidate_dict['addresses'][1]['id'],
            work_preference_id=candidate_dict['work_preference']['id'],
            work_experience_1_id=candidate_dict['work_experiences'][0]['id'],
            education_1_id=candidate_dict['educations'][0]['id'],
            degree_1_id=candidate_dict['educations'][0]['degrees'][0]['id'],
            military_1_id=candidate_dict['military_services'][0]['id'],
            preferred_location_1_id=candidate_dict['preferred_locations'][0]['id'],
            preferred_location_2_id=candidate_dict['preferred_locations'][1]['id'],
            skill_1_id=candidate_dict['skills'][0]['id'],
            skill_2_id=candidate_dict['skills'][1]['id'],
            social_1_id=candidate_dict['social_networks'][0]['id'],
            social_2_id=candidate_dict['social_networks'][1]['id']
    )

    # Create and update a Candidate
    update_resp = patch_to_candidate_resource(token, data)
    print response_info(update_resp)
    assert update_resp.status_code == 200


def test_update_candidate_without_id(sample_user, user_auth):
    """
    Test:   Attempt to update a Candidate without providing the ID
    Expect: 400
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Update Candidate's first_name
    data = {'candidate': {'first_name': fake.first_name()}}
    resp = patch_to_candidate_resource(token, data)

    print response_info(resp)
    assert resp.status_code == 400


def test_data_validations(sample_user, user_auth):
    """
    Test:   Validate json data
    Expect: 400
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    data = {'candidate': [{}]}
    resp = patch_to_candidate_resource(token, data)
    assert resp.status_code == 400
    print response_info(resp)

    data = {'candidates': {}}
    resp = patch_to_candidate_resource(token, data)
    assert resp.status_code == 400
    print response_info(resp)

    data = {'candidates': [{}]}
    resp = patch_to_candidate_resource(token, data)
    assert resp.status_code == 400
    print response_info(resp)

    data = {'candidates': [{'id': 5, 'phones': [{}]}]}
    resp = patch_to_candidate_resource(token, data)
    assert resp.status_code == 400
    print response_info(resp)

    data = {'candidates': [{'id': 5, 'phones': [{'id': 10, 'label': None, 'value': None, 'is_default': False}]}]}
    resp = patch_to_candidate_resource(token, data)
    assert resp.status_code == 403
    print response_info(resp)


def test_update_candidate_names(sample_user, user_auth):
    """
    Test:   Update candidate's first, middle, and last names
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(access_token=token)

    # Update Candidate's first_name
    candidate_id = create_resp.json()['candidates'][0]['id']
    data = {'candidates': [{'id': candidate_id, 'first_name': fake.first_name(),
                            'middle_name': fake.first_name(), 'last_name': fake.last_name()}
                           ]}
    update_resp = patch_to_candidate_resource(token, data)

    print response_info(update_resp)
    assert candidate_id == update_resp.json()['candidates'][0]['id']

    # Retrieve Candidate
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()

    # Assert on updated field
    f_name, l_name = data['candidates'][0]['first_name'], data['candidates'][0]['last_name']
    m_name = data['candidates'][0]['middle_name']
    full_name_from_data = str(f_name) + ' ' + str(m_name) + ' ' + str(l_name)
    assert candidate_dict['candidate']['full_name'] == full_name_from_data


######################## CandidateAddress ########################
def test_add_new_candidate_address(sample_user, user_auth):
    """
    Test:   Add a new CandidateAddress to an existing Candidate
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(access_token=token)

    # Add a new address to the existing Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    data = candidate_addresses(candidate_id=candidate_id)
    update_resp = patch_to_candidate_resource(token, data)
    print response_info(update_resp)

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    candidate_address = updated_candidate_dict['addresses'][0]
    assert updated_candidate_dict['id'] == candidate_id
    assert isinstance(candidate_address, dict)
    assert candidate_address['address_line_1'] == data['candidates'][0]['addresses'][0]['address_line_1']
    assert candidate_address['city'] == data['candidates'][0]['addresses'][0]['city']
    assert candidate_address['state'] == data['candidates'][0]['addresses'][0]['state']
    assert candidate_address['zip_code'] == data['candidates'][0]['addresses'][0]['zip_code']


def test_multiple_is_default_addresses(sample_user, user_auth):
    """
    Test:   Add more than one CandidateAddress with is_default set to True
    Expect: 200, but only one CandidateAddress must have is_default True, the rest must be False
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Add a new address to the existing Candidate with is_default set to True
    candidate_id = create_resp.json()['candidates'][0]['id']
    data = candidate_addresses(candidate_id=candidate_id)
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_can_addresses = updated_candidate_dict['addresses']
    # Only one of the addresses must be default!
    assert sum([1 for address in updated_can_addresses if address['is_default']]) == 1


def test_update_an_existing_address(sample_user, user_auth):
    """
    Test:   Update an existing CandidateAddress
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(access_token=token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_address = candidate_dict['addresses'][0]

    # Update one of Candidate's addresses
    data = candidate_addresses(candidate_id, candidate_address['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    updated_address = updated_candidate_dict['addresses'][0]
    assert isinstance(updated_candidate_dict, dict)
    assert updated_candidate_dict['id'] == candidate_id
    assert updated_address['address_line_1'] == data['candidates'][0]['addresses'][0]['address_line_1']
    assert updated_address['city'] == data['candidates'][0]['addresses'][0]['city']
    assert updated_address['state'] == data['candidates'][0]['addresses'][0]['state']
    assert updated_address['zip_code'] == data['candidates'][0]['addresses'][0]['zip_code']


def test_update_candidate_current_address(sample_user, user_auth):
    """
    Test:   Set one of candidate's addresses' is_default to True and assert it's the first
            CandidateAddress object returned in addresses-list
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(access_token=token)

    # Add another address
    candidate_id = create_resp.json()['candidates'][0]['id']
    data = candidate_addresses(candidate_id=candidate_id)
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    can_addresses = candidate_dict['addresses']

    # Update: Set the last CandidateAddress in can_addresses as the default candidate-address
    data = {'candidate': {'id': candidate_id, 'addresses': [{'id': can_addresses[-1]['id'], 'is_default': True}]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    updated_addresses = updated_candidate_dict['addresses']
    assert isinstance(updated_addresses, list)
    assert updated_addresses[0]['is_default'] == True


# TODO: add/update CandidateAddress with bad input/format, etc.
######################## CandidateAreaOfInterest ########################
def test_add_new_area_of_interest(sample_user, user_auth):
    """
    Test:   Add a new CandidateAreaOfInterest to existing Candidate.
            Number of CandidateAreaOfInterest should increase by 1.
    Expect: 200
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

    candidate_area_of_interest_count = len(candidate_dict['areas_of_interest'])

    # Add new CandidateAreaOfInterest
    data = candidate_areas_of_interest(sample_user.domain_id, candidate_id)
    resp = patch_to_candidate_resource(token, data)
    print response_info(resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_aois = candidate_dict['areas_of_interest']
    assert isinstance(candidate_aois, list)
    assert candidate_aois[0]['name'] == db.session.query(AreaOfInterest).get(candidate_aois[0]['id']).name
    assert candidate_aois[1]['name'] == db.session.query(AreaOfInterest).get(candidate_aois[1]['id']).name
    assert len(candidate_aois) == candidate_area_of_interest_count + 2


######################## CandidateEducation ########################
def test_add_new_education(sample_user, user_auth):
    """
    Test:   Add a new CandidateEducation. Candidate's CandidateEducation count should
            increase by 1.
    Expect: 200
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

    can_educations_count = len(candidate_dict['educations'])

    # Add new CandidateEducation
    data = candidate_educations(candidate_id)
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_educations = updated_can_dict['educations']

    can_ed_from_data = data['candidates'][0]['educations'][0]
    can_ed_degrees = can_ed_from_data['degrees'][0]
    can_ed_degree_bullets = can_ed_degrees['bullets'][0]

    assert candidate_id == updated_can_dict['id']
    assert isinstance(updated_educations, list)
    assert updated_educations[-1]['city'] == can_ed_from_data['city']
    assert updated_educations[-1]['school_name'] == can_ed_from_data['school_name']
    assert updated_educations[-1]['degrees'][-1]['type'] == can_ed_degrees['type']
    assert updated_educations[-1]['degrees'][-1]['title'] == can_ed_degrees['title']
    assert updated_educations[-1]['degrees'][-1]['bullets'][-1]['major'] == can_ed_degree_bullets['major']
    assert updated_educations[-1]['country'] == 'United States'
    assert len(updated_educations) == can_educations_count + 1


def test_update_education_of_a_diff_candidate(sample_user, user_auth):
    """
    Test:   Update education information of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    candidate_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve Candidate
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    # Update existing CandidateEducation of a different Candidate
    data = candidate_educations(7, candidate_dict['educations'][0]['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_update_education_primary_info(sample_user, user_auth):
    """
    Test:   Updates candidate's education's city, school_name, and state
            Since this is an update only, total number of candidate's education
            must remain unchanged.
    Expect: 200
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

    candidate_education_count = len(candidate_dict['educations'])

    # Update existing CandidateEducation
    data = candidate_educations(candidate_id, candidate_dict['educations'][0]['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    education_dict = updated_can_dict['educations'][0]

    can_ed_from_data = data['candidates'][0]['educations'][0]
    assert education_dict['city'] == can_ed_from_data['city']
    assert education_dict['state'] == can_ed_from_data['state']
    assert education_dict['school_name'] == can_ed_from_data['school_name']
    assert education_dict['country'] == 'United States'
    assert len(updated_can_dict['educations']) == candidate_education_count


def test_add_education_degree(sample_user, user_auth):
    """
    Test:   Add CandidateEducationDegree to an existing candidate's education.
            The number of CandidateEducationDegree must increase by 1 for this candidate.
    Expect: 200
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

    candidate_education_count = len(candidate_dict['educations'][0]['degrees'])

    # Update existing CandidateEducation
    data = {'candidates': [{'id': candidate_id, 'educations': [
        {'id': candidate_dict['educations'][0]['id'], 'degrees': [
            {'type': 'AA', 'title': 'associate', 'bullets': [
                {'major': 'mathematics', 'comments': 'obtained a high GPA whilst working full time'}
            ]}
        ]}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    education_dict = updated_can_dict['educations'][0]

    assert candidate_id == updated_can_dict['id']
    assert len(education_dict['degrees']) == candidate_education_count + 1
    assert education_dict['degrees'][-1]['type'] == 'AA'
    assert education_dict['degrees'][-1]['title'] == 'associate'
    assert education_dict['degrees'][-1]['bullets'][-1]['major'] == 'mathematics'


######################## CandidateExperience ########################
def test_add_candidate_experience(sample_user, user_auth):
    """
    Test:   Add a CandidateExperience to an existing Candidate. Number of Candidate's
            CandidateExperience must increase by 1.
    Expect:
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

    candidate_experience_count = len(candidate_dict['work_experiences'])

    # Add CandidateExperience
    data = candidate_experience(candidate_id)
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    can_experiences = updated_can_dict['work_experiences']

    can_experiences_from_data = data['candidates'][0]['work_experiences']

    assert candidate_id == updated_can_dict['id']
    assert isinstance(can_experiences, list)
    assert can_experiences[0]['organization'] == can_experiences_from_data[0]['organization']
    assert can_experiences[0]['position'] == can_experiences_from_data[0]['position']
    assert can_experiences[0]['city'] == can_experiences_from_data[0]['city']
    assert can_experiences[0]['state'] == can_experiences_from_data[0]['state']
    assert len(can_experiences) == candidate_experience_count + 1


def test_multiple_is_current_experiences(sample_user, user_auth):
    """
    Test:   Add more than one CandidateExperience with is_current set to True
    Expect: 200, but only one CandidateExperience must have is_current True, the rest must be False
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Add a new work experience to the existing Candidate with is_current set to True
    candidate_id = create_resp.json()['candidates'][0]['id']
    patch_to_candidate_resource(token, data=candidate_experience(candidate_id=candidate_id))

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_can_experiences = updated_candidate_dict['work_experiences']

    # Only one of the experiences must be current!
    assert sum([1 for experience in updated_can_experiences if experience['is_current']]) == 1


def test_add_experience_bullet(sample_user, user_auth):
    """
    Test:   Adds a CandidateExperienceBullet to an existing CandidateExperience
            Total number of candidate's experience_bullet must increase by 1, and
            number of candidate's CandidateExperience must remain unchanged.
    Expect: 200
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

    can_exp_count = len(candidate_dict['work_experiences'])
    can_exp_bullet_count = len(candidate_dict['work_experiences'][0]['bullets'])

    # Add CandidateExperienceBullet to existing CandidateExperience
    data = candidate_experience(candidate_id, candidate_dict['work_experiences'][0]['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_experiences = updated_can_dict['work_experiences']

    can_exp_bullet_from_data = data['candidates'][0]['work_experiences'][0]['bullets'][0]
    assert isinstance(updated_experiences, list)
    assert candidate_id == updated_can_dict['id']
    assert updated_experiences[0]['bullets'][-1]['description'] == can_exp_bullet_from_data['description']
    assert len(updated_experiences[0]['bullets']) == can_exp_bullet_count + 1
    assert len(updated_experiences) == len(updated_can_dict['work_experiences'])


def test_update_experience_bullet(sample_user, user_auth):
    """
    Test:   Update an existing CandidateExperienceBullet
            Since this is an update only, the number of candidate's experience_bullets
            must remain unchanged.
    Expect: 200
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

    experience_dict = candidate_dict['work_experiences'][0]
    candidate_experience_bullet_count = len(experience_dict['bullets'])

    # Update CandidateExperienceBullet
    data = candidate_experience(candidate_id=candidate_id, experience_id=experience_dict['id'],
                                experience_bullet_id=experience_dict['bullets'][0]['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_exp_bullet_dict = updated_can_dict['work_experiences'][0]['bullets']

    exp_bullet_dict_from_data = data['candidates'][0]['work_experiences'][0]['bullets'][0]

    assert candidate_experience_bullet_count == len(updated_exp_bullet_dict)
    assert updated_exp_bullet_dict[0]['description'] == exp_bullet_dict_from_data['description']


######################## CandidateWorkPreference ########################
def test_add_multiple_work_preference(sample_user, user_auth):
    """
    Test:   Attempt to add two CandidateWorkPreference
    Expect: 400
    :type sample_user:  User
    :type  user_auth:   UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    # Add CandidateWorkPreference
    data = candidate_work_preference(candidate_id)
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    assert updated_resp.status_code == 400


def test_update_work_preference(sample_user, user_auth):
    """
    Test:   Update existing CandidateWorkPreference. Since this is an update,
            number of CandidateWorkPreference must remain unchanged.
    Expect: 200
    :type sample_user:  User
    :type  user_auth:   UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    # Update CandidateWorkPreference
    data = candidate_work_preference(candidate_id, candidate_dict['work_preference']['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    work_preference_dict = candidate_dict['work_preference']

    work_pref_from_data = data['candidates'][0]['work_preference']

    assert candidate_id == candidate_dict['id']
    assert isinstance(work_preference_dict, dict)
    assert work_preference_dict['salary'] == work_pref_from_data['salary']
    assert work_preference_dict['hourly_rate'] == float(work_pref_from_data['hourly_rate'])
    assert work_preference_dict['travel_percentage'] == work_pref_from_data['travel_percentage']


######################## CandidateEmail ########################
def test_add_eamils(sample_user, user_auth):
    """
    Test:   Add an email to an existing Candidate. Number of candidate's emails must increase by 1.
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    emails = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']
    emails_count = len(emails)

    # Add new email
    data = candidate_emails(candidate_id)
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    emails = candidate_dict['emails']
    email_from_data = data['candidates'][0]['emails'][0]

    assert candidate_id == candidate_dict['id']
    assert emails[-1]['label'] == email_from_data['label'].capitalize()
    assert emails[-1]['address'] == email_from_data['address']
    assert len(emails) == emails_count + 1


def test_multiple_is_default_emails(sample_user, user_auth):
    """
    Test:   Add more than one CandidateEmail with is_default set to True
    Expect: 200, but only one CandidateEmail must have is_current True, the rest must be False
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Add a new email to the existing Candidate with is_current set to True
    candidate_id = create_resp.json()['candidates'][0]['id']
    patch_to_candidate_resource(token, data=candidate_emails(candidate_id=candidate_id))

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_can_emails = updated_candidate_dict['emails']

    # Only one of the emails must be default!
    assert sum([1 for email in updated_can_emails if email['is_default']]) == 1


def test_update_existing_email(sample_user, user_auth):
    """
    Test:   Update an existing CandidateEmail. Number of candidate's emails must remain unchanged
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    emails_before_update = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']
    emails_count_before_update = len(emails_before_update)

    # Update first email
    data = candidate_emails(candidate_id=candidate_id, email_id=emails_before_update[0]['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    emails_after_update = candidate_dict['emails']

    assert candidate_id == candidate_dict['id']
    assert emails_before_update[0]['id'] == emails_after_update[0]['id']
    assert emails_before_update[0]['address'] != emails_after_update[0]['address']
    assert emails_after_update[0]['address'] == data['candidates'][0]['emails'][0]['address']
    assert emails_count_before_update == len(emails_after_update)


def test_update_existing_email_with_bad_email_address(sample_user, user_auth):
    """
    Test:   Use a bad email address to update and existing CandidateEmail
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    emails_before_update = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']
    emails_count_before_update = len(emails_before_update)

    # Update first email with an invalid email address
    data = {'candidates': [{'id': candidate_id, 'emails': [
        {'id': emails_before_update[0]['id'], 'label': 'primary', 'address': 'bad_email.com'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    emails_after_update = candidate_dict['emails']
    assert updated_resp.status_code == 400
    assert candidate_id == candidate_dict['id']
    assert emails_count_before_update == len(emails_after_update)
    assert emails_before_update[0]['address'] == emails_after_update[0]['address']


######################## CandidatePhone ########################
def test_add_candidate_phones(sample_user, user_auth):
    """
    Test:   Add CandidatePhone to an existing Candidate. Number of candidate's phones must increase by 1.
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    phones_before_update = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones']
    phones_count_before_update = len(phones_before_update)

    # Add new email
    data = candidate_phones(candidate_id)
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    phones_after_update = candidate_dict['phones']
    phones_from_data = data['candidates'][0]['phones']

    assert candidate_id == candidate_dict['id']
    assert phones_after_update[-1]['label'] == phones_from_data[0]['label'].capitalize()
    assert len(phones_after_update) == phones_count_before_update + 1


def test_multiple_is_default_phones(sample_user, user_auth):
    """
    Test:   Add more than one CandidatePhone with is_default set to True
    Expect: 200, but only one CandidatePhone must have is_current True, the rest must be False
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Add a new email to the existing Candidate with is_current set to True
    candidate_id = create_resp.json()['candidates'][0]['id']
    patch_to_candidate_resource(token, data=candidate_phones(candidate_id=candidate_id))

    # Retrieve Candidate after update
    updated_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    updated_can_phones = updated_candidate_dict['phones']

    # Only one of the phones must be default!
    assert sum([1 for phone in updated_can_phones if phone['is_default']]) == 1


def test_update_existing_phone(sample_user, user_auth):
    """
    Test:   Update an existing CandidatePhone. Number of candidate's phones must remain unchanged.
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    phones_before_update = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones']
    phones_count_before_update = len(phones_before_update)

    # Update first phone
    data = candidate_phones(candidate_id=candidate_id, phone_id=phones_before_update[0]['id'])
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    phones_after_update = candidate_dict['phones']

    assert candidate_id == candidate_dict['id']
    assert phones_before_update[0]['id'] == phones_after_update[0]['id']
    assert phones_before_update[0]['value'] != phones_after_update[0]['value']
    assert phones_count_before_update == len(phones_after_update)


######################## CandidateMilitaryService ########################
def test_add_military_service(sample_user, user_auth):
    """
    Test:   Add a CandidateMilitaryService to an existing Candidate.
            Number of candidate's military_services should increase by 1.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    military_services_before_update = get_from_candidate_resource(token, candidate_id). \
        json()['candidate']['military_services']
    military_services_count_before_update = len(military_services_before_update)

    # Add CandidateMilitaryService
    data = {'candidates': [{'id': candidate_id, 'military_services': [
        {'country': 'gb', 'branch': 'air force', 'comments': 'adept at killing cows with mad-cow-disease'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    military_services_after_update = candidate_dict['military_services']
    assert candidate_id == candidate_dict['id']
    assert len(military_services_after_update) == military_services_count_before_update + 1
    assert military_services_after_update[-1]['branch'] == 'air force'
    assert military_services_after_update[-1]['comments'] == 'adept at killing cows with mad-cow-disease'


def test_update_military_service(sample_user, user_auth):
    """
    Test:   Update an existing CandidateMilitaryService.
            Number of candidate's military_services should remain unchanged.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    military_services_before_update = get_from_candidate_resource(token, candidate_id). \
        json()['candidate']['military_services']
    military_services_count_before_update = len(military_services_before_update)

    # Add CandidateMilitaryService
    data = {'candidates': [{'id': candidate_id, 'military_services': [
        {'id': military_services_before_update[0]['id'], 'country': 'gb', 'branch': 'air force',
         'comments': 'adept at killing cows with mad-cow-disease'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    military_services_after_update = candidate_dict['military_services']
    assert candidate_id == candidate_dict['id']
    assert len(military_services_after_update) == military_services_count_before_update
    assert military_services_after_update[0]['branch'] == 'air force'
    assert military_services_after_update[0]['comments'] == 'adept at killing cows with mad-cow-disease'


######################## CandidatePreferredLocation ########################
def test_add_preferred_location(sample_user, user_auth):
    """
    Test:   Add a CandidatePreferredLocation to an existing Candidate.
            Number of candidate's preferred_location should increase by 1.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    preferred_location_before_update = get_from_candidate_resource(token, candidate_id). \
        json()['candidate']['preferred_locations']
    preferred_locations_count_before_update = len(preferred_location_before_update)

    # Add CandidatePreferredLocation
    data = {'candidates': [{'id': candidate_id, 'preferred_locations': [
        {'city': 'austin', 'state': 'texas'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    preferred_locations_after_update = candidate_dict['preferred_locations']
    assert candidate_id == candidate_dict['id']
    assert len(preferred_locations_after_update) == preferred_locations_count_before_update + 1
    assert preferred_locations_after_update[-1]['city'] == 'austin'
    assert preferred_locations_after_update[-1]['state'] == 'texas'


def test_update_preferred_location(sample_user, user_auth):
    """
    Test:   Update an existing CandidatePreferredLocation.
            Number of candidate's preferred_location should remain unchanged.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    preferred_location_before_update = get_from_candidate_resource(token, candidate_id). \
        json()['candidate']['preferred_locations']
    preferred_locations_count_before_update = len(preferred_location_before_update)

    # Add CandidatePreferredLocation
    data = {'candidates': [{'id': candidate_id, 'preferred_locations': [
        {'id': preferred_location_before_update[0]['id'], 'city': 'austin', 'state': 'texas'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    preferred_locations_after_update = candidate_dict['preferred_locations']
    assert candidate_id == candidate_dict['id']
    assert len(preferred_locations_after_update) == preferred_locations_count_before_update + 0
    assert preferred_locations_after_update[0]['city'] == 'austin'
    assert preferred_locations_after_update[0]['state'] == 'texas'


######################## CandidateSkill ########################
def test_add_skill(sample_user, user_auth):
    """
    Test:   Add a CandidateSkill to an existing Candidate.
            Number of candidate's preferred_location should increase by 1.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    skills_before_update = get_from_candidate_resource(token, candidate_id).json()['candidate']['skills']
    skills_count_before_update = len(skills_before_update)

    # Add CandidateSkill
    data = {'candidates': [{'id': candidate_id, 'skills': [{'name': 'pos'}]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    skills_after_update = candidate_dict['skills']
    assert candidate_id == candidate_dict['id']
    assert len(skills_after_update) == skills_count_before_update + 1
    assert skills_after_update[-1]['name'] == 'pos'


def test_update_skill(sample_user, user_auth):
    """
    Test:   Update an existing CandidateSkill.
            Number of candidate's preferred_location should remain unchanged.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    skills_before_update = get_from_candidate_resource(token, candidate_id).json()['candidate']['skills']
    skills_count_before_update = len(skills_before_update)

    # Update CandidateSkill
    data = {'candidates': [{'id': candidate_id, 'skills': [
        {'id': skills_before_update[0]['id'], 'name': 'pos'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    skills_after_update = candidate_dict['skills']
    assert candidate_id == candidate_dict['id']
    assert len(skills_after_update) == skills_count_before_update
    assert skills_after_update[0]['name'] == 'pos'


######################## CandidateSocialNetwork ########################
def test_add_social_network(sample_user, user_auth):
    """
    Test:   Add a CandidateSocialNetwork to an existing Candidate.
            Number of candidate's social_networks should increase by 1.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    social_networks_before_update = get_from_candidate_resource(token, candidate_id). \
        json()['candidate']['social_networks']
    social_networks_count_before_update = len(social_networks_before_update)

    # Add CandidateSocialNetwork
    data = {'candidates': [{'id': candidate_id, 'social_networks': [
        {'name': 'linkedin', 'profile_url': 'https://www.linkedin.com/company/sara'}
    ]}]}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    social_networks_after_update = candidate_dict['social_networks']
    assert candidate_id == candidate_dict['id']
    assert len(social_networks_after_update) == social_networks_count_before_update + 1
    assert social_networks_after_update[-1]['name'] == 'LinkedIn'
    assert social_networks_after_update[-1]['profile_url'] == 'https://www.linkedin.com/company/sara'


def test_update_social_network(sample_user, user_auth):
    """
    Test:   Update a CandidateSocialNetwork.
            Number of candidate's social_networks should remain unchanged.
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']

    social_networks_before_update = get_from_candidate_resource(token, candidate_id). \
        json()['candidate']['social_networks']
    social_networks_count_before_update = len(social_networks_before_update)

    # Add CandidateSocialNework
    data = {'candidate': {'id': candidate_id, 'social_networks': [
        {'id': social_networks_before_update[0]['id'],
         'name': 'linkedin', 'profile_url': 'https://www.linkedin.com/company/sara'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    social_networks_after_update = candidate_dict['social_networks']
    assert candidate_id == candidate_dict['id']
    assert len(social_networks_after_update) == social_networks_count_before_update
    assert social_networks_after_update[0]['name'] == 'Facebook'
    assert social_networks_after_update[0]['profile_url'] == 'http://www.facebook.com/1024359318'
