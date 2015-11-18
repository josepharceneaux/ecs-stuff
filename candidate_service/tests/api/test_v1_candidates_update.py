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
    update_candidate, patch_to_candidate_resource, candidate_data_for_update
)

######################## Candidate ########################
def test_update_candidate(sample_user, user_auth):
    """
    Test:   Update an existing Candidate
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)
    candidate_id = create_resp.json()['candidates'][0]['id']

    # Retrieve Candidate
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
        skill_3_id=candidate_dict['skills'][2]['id'],
        social_1_id=candidate_dict['social_networks'][0]['id'],
        social_2_id=candidate_dict['social_networks'][1]['id']
    )
    update_resp = patch_to_candidate_resource(token, data)

    print response_info(update_resp.request, update_resp.json(), update_resp.status_code)
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
    data = {'candidate': {'first_name': 'larry'}}
    resp = patch_to_candidate_resource(token, data)

    print response_info(resp.request, resp.json(), resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp.json()


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
    data = {'candidate':
                {'id': candidate_id, 'first_name': 'larry',
                 'middle_name': 'james', 'last_name': 'david'}
            }
    update_resp = patch_to_candidate_resource(token, data)

    print response_info(update_resp.request, update_resp.json(),
                        update_resp.status_code)
    assert candidate_id == update_resp.json()['candidates'][0]['id']

    # Retrieve Candidate
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()

    # Assert on updated field
    assert candidate_dict['candidate']['full_name'] == 'Larry David'

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
    data = {'candidate': {'id': candidate_id, 'addresses': [
        {'address_line_1': '225 W. Santa Clara St.', 'city': 'san jose',
         'state': 'ca', 'zip_code': '95113'}
    ]}}
    update_resp = patch_to_candidate_resource(token, data)
    print response_info(update_resp.request, update_resp.json(),
                        update_resp.status_code)

    # Retrieve Candidate after update
    updated_candidate = get_from_candidate_resource(token, candidate_id).json()

    # Since this is a new address, it will the last object in candidate_address
    candidate_address = updated_candidate['candidate']['addresses'][-1]
    assert updated_candidate['candidate']['id'] == candidate_id
    assert candidate_address['address_line_1'] == '225 W. Santa Clara St.'
    assert candidate_address['city'] == 'san jose'
    assert candidate_address['state'] == 'ca'
    assert candidate_address['zip_code'] == '95113'
    assert candidate_address['country'] == 'United States'


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
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()
    candidate_address = candidate_dict['candidate']['addresses'][0]

    # Update one of Candidate's addresses
    data = {'candidate': {'id': candidate_id, 'addresses': [
        {'id': candidate_address['id'],
         'address_line_1': '225 W. Santa Clara St.', 'city': 'san jose',
         'state': 'ca', 'zip_code': '95113'}
    ]}}
    update_resp = patch_to_candidate_resource(token, data)
    print response_info(update_resp.request, update_resp.json(), update_resp.status_code)

    # Retrieve Candidate after updating
    updated_candidate = get_from_candidate_resource(token, candidate_id).json()
    # Updated address
    updated_address = updated_candidate['candidate']['addresses'][0]

    assert updated_candidate['candidate']['id'] == candidate_id
    assert updated_address['address_line_1'] == '225 W. Santa Clara St.'
    assert updated_address['city'] == 'san jose'
    assert updated_address['state'] == 'ca'
    assert updated_address['zip_code'] == '95113'
    assert updated_address['country'] == 'United States'


def test_add_address_to_existing_candidate(sample_user, user_auth):
    """
    Test:   Add CandidateAddress to existing Candidate
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
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()

    # Add new CandidateAddress
    data = {'candidate': {'id': candidate_id, 'addresses': [
        {'address_line_1': '675 Saratoga Ave', 'city': 'san jose', 'state': 'ca', 'zip_code': '95129'}
    ]}}
    add_resp = patch_to_candidate_resource(token, data)
    print response_info(add_resp.request, add_resp.json(), add_resp.status_code)

    # Retrieve Candidate after adding new address
    updated_candidate = get_from_candidate_resource(token, candidate_id).json()
    # Newly added address
    address = updated_candidate['candidate']['addresses'][-1]

    assert updated_candidate['candidate']['id'] == candidate_id
    assert address['address_line_1'] == '675 Saratoga Ave'
    assert address['city'] == 'san jose'
    assert address['state'] == 'ca'
    assert address['zip_code'] == '95129'
    assert address['country'] == 'United States'

######################## CandidateAreaOfInterest ########################
def test_add_new_area_of_interest(sample_user, user_auth):
    """
    Test:   Add a new CandidateAreaOfInterest
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

    # Add new CandidateAreaOfInterest
    data = {'candidate': {'id': candidate_id, 'areas_of_interest': [
        {'description': 'programming'}, {'description': 'teaching'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    updated_resp_dict = get_from_candidate_resource(token, candidate_id).json()
    updated_candidate_dict = updated_resp_dict['candidate']
    updated_aoi_list = updated_candidate_dict['areas_of_interest']

    assert candidate_id == updated_candidate_dict['id']
    assert 'teaching' or 'programming' in updated_aoi_list[0].values()
    assert 'teaching' or 'programming' in updated_aoi_list[1].values()

######################## CandidateCustomField ########################
# TODO: complete test after user-api is available
# def test_add_new_custom_field(sample_user, user_auth):
#     """
#     Test:   Add a new CandidateCustomField to an existing Candidate.
#             Candidate's custom_field should increase by 1.
#     Expect: 200
#     :type sample_user:  User
#     :type user_auth:    UserAuthentication
#     """
#     # Get access token
#     token = user_auth.get_auth_token(sample_user, True)['access_token']
#
#     # Create Candidate
#     create_resp = post_to_candidate_resource(token)
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     custom_fields_before_update = candidate_dict['custom_fields']
#     custom_fields_count_before_update = len(custom_fields_before_update)
#
#     # Add new CandidateCustomField
#     data = {'candidate': {'id': candidate_id, 'custom_fields': [
#         {'custom_field_id':'', 'value': 'entrepreneur'}
#     ]}}
#     updated_resp = patch_to_candidate_resource(token, data)
#     print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)
#
#     # Retrieve updated Candidate
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     custom_fileds_after_update = candidate_dict['custom_fields']
#     print "\nbefore = %s" % custom_fields_before_update
#     print "\nafter = %s" % custom_fileds_after_update

######################## CandidateEducation ########################
def test_add_new_education(sample_user, user_auth):
    """
    Test:   Add a new CandidateAreaOfInterest
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

    # Add new CandidateEducation
    data = {'candidate': {'id': candidate_id, 'educations': [
        {'school_name': 'uc berkeley', 'city': 'berkeley', 'degrees': [
            {'type': 'bs', 'title': 'science', 'degree_bullets': [
                {'major': 'biology'}
            ]}
        ]}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    education_dict = updated_can_dict['educations'][-1]

    assert candidate_id == updated_can_dict['id']
    assert education_dict['city'] == 'berkeley'
    assert education_dict['country'] == 'United States'
    assert education_dict['school_name'] == 'uc berkeley'
    assert education_dict['degrees'][-1]['type'] == 'bs'
    assert education_dict['degrees'][-1]['title'] == 'science'
    assert education_dict['degrees'][-1]['degree_bullets'][-1]['major'] == 'biology'


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
    data = {'candidate': {'id':  candidate_id, 'educations': [
        {'id': candidate_dict['educations'][0]['id'], 'school_name': 'chico state',
         'city': 'chico', 'state': 'ca', 'country': 'us'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    education_dict = updated_can_dict['educations'][0]

    assert education_dict['city'] == 'chico'
    assert education_dict['state'] == 'ca'
    assert education_dict['country'] == 'United States'
    assert education_dict['school_name'] == 'chico state'
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
    data = {'candidate': {'id':  candidate_id, 'educations': [
        {'id': candidate_dict['educations'][0]['id'], 'degrees': [
            {'type': 'AA', 'title': 'associate', 'degree_bullets': [
                {'major': 'mathematics', 'comments': 'obtained a high GPA whilst working full time'}
            ]}
        ]}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    education_dict = updated_can_dict['educations'][0]
    print "\neducation_dict = %s" % education_dict

    assert candidate_id == updated_can_dict['id']
    assert len(education_dict['degrees']) == candidate_education_count + 1
    assert education_dict['degrees'][-1]['type'] == 'AA'
    assert education_dict['degrees'][-1]['title'] == 'associate'
    assert education_dict['degrees'][-1]['degree_bullets'][-1]['major'] == 'mathematics'

######################## CandidateWorkExperience ########################
def test_add_experience_bullet(sample_user, user_auth):
    """
    Test:   Adds a CandidateExperienceBullet to an existing CandidateExperience
            Since this is a new addition, total number of candidate's experience_bullet
            must increase by 1.
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

    candidate_experience_bullet_count = len(candidate_dict['work_experiences'][0]['experience_bullets'])

    # Add CandidateExperienceBullet to existing CandidateExperience
    data = {'candidate': {'id': candidate_id, 'work_experiences': [
        {'id': candidate_dict['work_experiences'][0]['id'],
         'experience_bullets': [{'description': 'managing group lunch orders'}]}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    experience_dict = updated_can_dict['work_experiences'][0]

    assert candidate_id == updated_can_dict['id']
    assert experience_dict['experience_bullets'][-1]['description'] == 'managing group lunch orders'
    assert len(experience_dict['experience_bullets']) == candidate_experience_bullet_count + 1


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
    candidate_experience_bullet_count = len(experience_dict['experience_bullets'])

    # Update CandidateExperienceBullet
    data = {'candidate': {'id': candidate_id, 'work_experiences': [
        {'id': experience_dict['id'], 'experience_bullets': [
            {'id': experience_dict['experience_bullets'][0]['id'], 'description': 'ruby on rails'}
        ]}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    updated_can_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    experience_bullet_dict = updated_can_dict['work_experiences'][0]['experience_bullets']

    assert candidate_experience_bullet_count == len(experience_bullet_dict)
    assert experience_bullet_dict[0]['description'] == 'ruby on rails'

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
    data = {'candidate': {'id': candidate_id, 'work_preference': {
        'work_preference': {'telecommute': True, 'travel_percentage': 10, 'hourly_rate': 35}
    }}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

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
    data = {'candidate': {'id': candidate_id, 'work_preference': {
        'id': candidate_dict['work_preference']['id'], 'telecommute': True,
        'travel_percentage': 10, 'hourly_rate': 35, 'salary': 70000, 'third_party': 'true'
    }}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    print "\ncan_dict = %s" % candidate_dict
    work_preference_dict = candidate_dict['work_preference']

    assert candidate_id == candidate_dict['id']
    assert work_preference_dict['salary'] == 70000.0
    assert work_preference_dict['hourly_rate'] == 35.0
    assert work_preference_dict['travel_percentage'] == 10

######################## CandidateEmail ########################
def test_add_eamils(sample_user, user_auth):
    """
    Test:   Add two emails to an existing Candidate. Number of candidate's emails must increase by 2
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
    data = {'candidate': {'id': candidate_id, 'emails': [
        {'label': 'work', 'address': 'amir@gettalent.com'},
        {'label': 'primary', 'address': 'amir@baws.com'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    emails = candidate_dict['emails']
    assert candidate_id == candidate_dict['id']
    assert emails[-1]['label'] == 'Primary'
    assert emails[-1]['address'] == 'amir@baws.com'
    assert emails[-2]['label'] == 'Work'
    assert emails[-2]['address'] == 'amir@gettalent.com'
    assert len(emails) == emails_count + 2


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
    data = {'candidate': {'id': candidate_id, 'emails': [
        {'id': emails_before_update[0]['id'], 'label': 'primary', 'address': 'karen@karen.com'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    emails_after_update = candidate_dict['emails']
    assert candidate_id == candidate_dict['id']
    assert emails_before_update[0]['id'] == emails_after_update[0]['id']
    assert emails_before_update[0]['address'] != emails_after_update[0]['address']
    assert emails_after_update[0]['address'] == 'karen@karen.com'
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
    data = {'candidate': {'id': candidate_id, 'emails': [
        {'id': emails_before_update[0]['id'], 'label': 'primary', 'address': 'bad_email.com'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    emails_after_update = candidate_dict['emails']
    assert updated_resp.status_code == 400
    assert candidate_id == candidate_dict['id']
    assert emails_count_before_update == len(emails_after_update)
    assert emails_before_update[0]['address'] == emails_after_update[0]['address']

######################## CandidatePhone ########################
def test_add_phones(sample_user, user_auth):
    """
    Test:   Add two phones to an existing Candidate. Number of candidate's phones must increase by 2
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
    data = {'candidate': {'id': candidate_id, 'phones': [
        {'label': 'mobile', 'value': '4087756787'},
        {'label': 'home', 'value': '5109989845'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    phones_after_update = candidate_dict['phones']
    assert candidate_id == candidate_dict['id']
    assert phones_after_update[-1]['label'] == 'Home'
    assert phones_after_update[-1]['value'] == '5109989845'
    assert phones_after_update[-2]['label'] == 'Mobile'
    assert phones_after_update[-2]['value'] == '4087756787'
    assert len(phones_after_update) == phones_count_before_update + 2


def test_update_existing_phone(sample_user, user_auth):
    """
    Test:   Update an existing CandidatePhone. Number of candidate's phones must remain unchanged
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

    # Update first email
    data = {'candidate': {'id': candidate_id, 'phones': [
        {'id': phones_before_update[0]['id'], 'label': 'other', 'value': '1-800-9346489'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    phones_after_update = candidate_dict['phones']
    assert candidate_id == candidate_dict['id']
    assert phones_before_update[0]['id'] == phones_after_update[0]['id']
    assert phones_before_update[0]['value'] != phones_after_update[0]['value']
    assert phones_after_update[0]['value'] == '1-800-9346489'
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

    military_services_before_update = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services']
    military_services_count_before_update = len(military_services_before_update)

    # Add CandidateMilitaryService
    data = {'candidate': {'id': candidate_id, 'military_services': [
        {'country': 'gb', 'branch': 'air force', 'comments': 'adept at killing cows with mad-cow-disease'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    military_services_after_update = candidate_dict['military_services']
    assert candidate_id == candidate_dict['id']
    assert len(military_services_after_update) == military_services_count_before_update + 1
    assert military_services_after_update[-1]['country'] == 'United Kingdom'
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

    military_services_before_update = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services']
    military_services_count_before_update = len(military_services_before_update)

    # Add CandidateMilitaryService
    data = {'candidate': {'id': candidate_id, 'military_services': [
        {'id': military_services_before_update[0]['id'], 'country': 'gb', 'branch': 'air force',
         'comments': 'adept at killing cows with mad-cow-disease'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    military_services_after_update = candidate_dict['military_services']
    assert candidate_id == candidate_dict['id']
    assert len(military_services_after_update) == military_services_count_before_update
    assert military_services_after_update[0]['country'] == 'United Kingdom'
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

    preferred_location_before_update = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations']
    preferred_locations_count_before_update = len(preferred_location_before_update)

    # Add CandidatePreferredLocation
    data = {'candidate': {'id': candidate_id, 'preferred_locations': [
        {'city': 'austin', 'region': 'texas'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    preferred_locations_after_update = candidate_dict['preferred_locations']
    assert candidate_id == candidate_dict['id']
    assert len(preferred_locations_after_update) == preferred_locations_count_before_update + 1
    assert preferred_locations_after_update[-1]['city'] == 'austin'
    assert preferred_locations_after_update[-1]['region'] == 'texas'


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

    preferred_location_before_update = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations']
    preferred_locations_count_before_update = len(preferred_location_before_update)

    # Add CandidatePreferredLocation
    data = {'candidate': {'id': candidate_id, 'preferred_locations': [
        {'id': preferred_location_before_update[0]['id'], 'city': 'austin', 'region': 'texas'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    preferred_locations_after_update = candidate_dict['preferred_locations']
    assert candidate_id == candidate_dict['id']
    assert len(preferred_locations_after_update) == preferred_locations_count_before_update + 0
    assert preferred_locations_after_update[0]['city'] == 'austin'
    assert preferred_locations_after_update[0]['region'] == 'texas'

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
    data = {'candidate': {'id': candidate_id, 'skills': [{'name': 'pos'}]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    skills_after_update = candidate_dict['skills']
    assert candidate_id == candidate_dict['id']
    assert len(skills_after_update) ==  skills_count_before_update + 1
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
    data = {'candidate': {'id': candidate_id, 'skills': [
        {'id': skills_before_update[0]['id'], 'name': 'pos'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    skills_after_update = candidate_dict['skills']
    assert candidate_id == candidate_dict['id']
    assert len(skills_after_update) ==  skills_count_before_update
    assert skills_after_update[0]['name'] == 'pos'

######################## CandidateSkill ########################
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

    social_networks_before_update = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['social_networks']
    social_networks_count_before_update = len(social_networks_before_update)

    # Add CandidateSocialNework
    data = {'candidate': {'id': candidate_id, 'social_networks': [
        {'name': 'linkedin', 'profile_url': 'https://www.linkedin.com/company/sara'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    social_networks_after_update = candidate_dict['social_networks']
    assert candidate_id == candidate_dict['id']
    assert len(social_networks_after_update) ==  social_networks_count_before_update + 1
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

    social_networks_before_update = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['social_networks']
    social_networks_count_before_update = len(social_networks_before_update)

    # Add CandidateSocialNework
    data = {'candidate': {'id': candidate_id, 'social_networks': [
        {'id': social_networks_before_update[0]['id'],
         'name': 'linkedin', 'profile_url': 'https://www.linkedin.com/company/sara'}
    ]}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    social_networks_after_update = candidate_dict['social_networks']
    assert candidate_id == candidate_dict['id']
    assert len(social_networks_after_update) ==  social_networks_count_before_update
    assert social_networks_after_update[0]['name'] == 'LinkedIn'
    assert social_networks_after_update[0]['profile_url'] == 'https://www.linkedin.com/company/sara'
