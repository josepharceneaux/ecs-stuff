"""
Test cases for CandidateResource/delete()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User

# Conftest
from common.tests.conftest import UserAuthentication
from common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    update_candidate, patch_to_candidate_resource
)

########################################################################
def test_update_candidate(sample_user, user_auth):
    """
    Test:   Update an existing Candidate
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Update Candidate
    resp = update_candidate(access_token=token)

    resp_dict = resp.json()
    print response_info(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 200
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


def test_update_candidate_without_id(sample_user, user_auth):
    """
    Test:   Attempt to update a Candidate without providing the ID
    Expect: 400
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
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
    # Get auth token
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


def test_add_new_candidate_address(sample_user, user_auth):
    """
    Test:   Add a new CandidateAddress to an existing Candidate
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
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
    # Get auth token
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
    # Get auth token
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
    print "\ndata = %s" % data
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


# def test_add_new_custom_field(sample_user, user_auth):
#     """
#     Test:   Add a new CandidateAreaOfInterest
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
#
#     # Add new CandidateCustomField
#     data = {'candidate': {'id': candidate_id, 'custom_fields': [
#         {''}
#     ]}}


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

    print "\ncan_dict = %s" % candidate_dict

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
    candiadte_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candiadte_id).json()['candidate']

    # Update CandidateWorkPreference
    data = {'candidate': {'id': candiadte_id, 'work_preference': {
        'id': candidate_dict['work_preference']['id'], 'telecommute': True,
        'travel_percentage': 10, 'hourly_rate': 35, 'salary': 70000, 'third_party': 'true'
    }}}
    updated_resp = patch_to_candidate_resource(token, data)
    print response_info(updated_resp.request, updated_resp.json(), updated_resp.status_code)

    # Retrieve Candidate after update
    candidate_dict = get_from_candidate_resource(token, candiadte_id).json()['candidate']
    work_preference_dict = candidate_dict['work_preference']

    print "\nwork_pref_dict = %s" % work_preference_dict

    assert candiadte_id == candidate_dict['id']
    assert work_preference_dict['salary'] == 70000.0
    assert work_preference_dict['hourly_rate'] == 35.0
    assert work_preference_dict['travel_percentage'] == 10

