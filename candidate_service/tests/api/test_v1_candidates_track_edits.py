"""
Test cases pertaining to CandidateEditResource
"""
# Candidate Service app instance
from candidate_service.candidate_app import app
# Conftest
from candidate_service.common.tests.conftest import *
# Helper functions
from helpers import (
    response_info, request_to_candidate_resource, request_to_candidates_resource,
    request_to_candidate_edit_resource, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
# Custom error
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


def test_edit_candidate_primary_info(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's first, middle, and last names
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']

    # Update Candidate's first and last names
    data = {'candidates': [
        {'id': candidate_id, 'first_name': 'Quentin', 'middle_name': 'Jerome', 'last_name': 'Tarantino'}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate
    new_candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_candidate_dict['full_name']
    assert candidate_edits[0]['new_value'] == new_candidate_dict['full_name']


def test_edit_candidate_address(access_token_first, user_first, talent_pool):
    """
    Test:   Edit Candidate's address
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_address_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['addresses'][0]

    # Update Candidate's address
    data = {'candidates': [
        {'id': candidate_id, 'addresses': [
            {'id': old_address_dict['id'], 'address_line_1': '255 west santa clara'}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate addresses
    new_address_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['addresses'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_address_dict['address_line_1'] != old_address_dict['address_line_1']
    assert candidate_edits[0]['old_value'] == old_address_dict['address_line_1']
    assert candidate_edits[0]['new_value'] == new_address_dict['address_line_1']


def test_edit_candidate_custom_field(access_token_first, user_first, talent_pool,
                                     domain_custom_fields):
    """
    Test:   Change Candidate's custom fields
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_custom_field_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['custom_fields'][0]
    db.session.commit()

    # Update Candidate's custom field
    data = {'candidates': [
        {'id': candidate_id, 'custom_fields': [
            {'id': old_custom_field_dict['id'], 'value': 'foobar'}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate custom fields
    new_custom_field_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['custom_fields'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)
    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_custom_field_dict['value']
    assert candidate_edits[0]['new_value'] == new_custom_field_dict['value']


def test_edit_candidate_education(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's education records
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_education_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['educations'][0]

    # Update Candidate's education
    data = {'candidates': [
        {'id': candidate_id, 'educations': [
            {'id': old_education_dict['id'], 'school_name': 'UC Davis'}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate educations
    new_education_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['educations'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)
    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_education_dict['school_name'] != old_education_dict['school_name']
    assert candidate_edits[0]['old_value'] == old_education_dict['school_name']
    assert candidate_edits[0]['new_value'] == new_education_dict['school_name']


def test_edit_candidate_education_degree(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's education degree records
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_education_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['educations'][0]

    # Update Candidate's education degree
    data = {'candidates': [
        {'id': candidate_id, 'educations': [
            {'id': old_education_dict['id'], 'degrees': [
                {'id': old_education_dict['degrees'][0]['id'], 'type': 'MS', 'title': 'Biomedical Engineering'}
            ]}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate education
    new_education_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['educations'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_education_dict['degrees'][0]['type'] != old_education_dict['degrees'][0]['type']
    assert new_education_dict['degrees'][0]['title'] != old_education_dict['degrees'][0]['title']
    assert candidate_edits[0]['old_value'] == old_education_dict['degrees'][0]['type']
    assert candidate_edits[0]['new_value'] == new_education_dict['degrees'][0]['type']
    assert candidate_edits[1]['old_value'] == old_education_dict['degrees'][0]['title']
    assert candidate_edits[1]['new_value'] == new_education_dict['degrees'][0]['title']


def test_edit_candidate_education_degree_bullet(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's education degree bullet records
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_education_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['educations'][0]
    old_degree_bullet_dict = old_education_dict['degrees'][0]['bullets'][0]

    # Update Candidate's education degree bullet
    data = {'candidates': [
        {'id': candidate_id, 'educations': [
            {'id': old_education_dict['id'], 'degrees': [
                {'id': old_education_dict['degrees'][0]['id'], 'bullets': [
                    {'id': old_degree_bullet_dict['id'], 'major': 'nursing'}
                ]}
            ]}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate education
    new_education_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['educations'][0]
    new_degree_bullet_dict = new_education_dict['degrees'][0]['bullets'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_degree_bullet_dict['major'] != old_degree_bullet_dict['major']
    assert candidate_edits[0]['old_value'] == old_degree_bullet_dict['major']
    assert candidate_edits[0]['new_value'] == new_degree_bullet_dict['major']


def test_edit_candidate_experience(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's experience records
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_experience_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['work_experiences'][0]

    # Update Candidate's experience
    data = {'candidates': [
        {'id': candidate_id, 'work_experiences': [
            {'id': old_experience_dict['id'], 'organization': 'Dice', 'position': 'Software Engineer'}
        ]}
    ]}
    updated_resp = request_to_candidates_resource(access_token_first, 'patch', data)
    print response_info(updated_resp)

    # Retrieve Candidate
    new_experience_dict = request_to_candidate_resource(
        access_token_first, 'get', candidate_id).json()['candidate']['work_experiences'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_experience_dict['organization'] != old_experience_dict['organization']
    assert new_experience_dict['position'] != old_experience_dict['position']
    assert candidate_edits[-2]['old_value'] == old_experience_dict['position']
    assert candidate_edits[-2]['new_value'] == new_experience_dict['position']
    assert candidate_edits[-1]['old_value'] == old_experience_dict['organization']
    assert candidate_edits[-1]['new_value'] == new_experience_dict['organization']


def test_edit_candidate_experience_bullet(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's experience bullet records
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_experience_dict = request_to_candidate_resource(
            access_token_first, 'get', candidate_id).json()['candidate']['work_experiences'][0]
    old_experience_bullet_dict = old_experience_dict['bullets'][0]

    # Update Candidate's experience bullet
    data = {'candidates': [
        {'id': candidate_id, 'work_experiences': [
            {'id': old_experience_dict['id'], 'bullets': [
                {'id': old_experience_bullet_dict['id'], 'description': 'job sucked'}
            ]}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate
    new_experience_dict = request_to_candidate_resource(
            access_token_first, 'get', candidate_id).json()['candidate']['work_experiences'][0]
    new_experience_bullet_dict = new_experience_dict['bullets'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[-1]['old_value'] == old_experience_bullet_dict['description']
    assert candidate_edits[-1]['new_value'] == new_experience_bullet_dict['description']


def test_edit_candidate_work_preference(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's work preference records
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_work_pref_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['work_preference']

    # Update Candidate's work preference
    data = {'candidates': [
        {'id': candidate_id, 'work_preference': {
            'id': old_work_pref_dict['id'], 'salary': '150000', 'hourly_rate': '75'
        }}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate
    new_work_pref_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['work_preference']

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert int(float(candidate_edits[0]['old_value'])) == int(float(old_work_pref_dict['salary']))
    assert int(float(candidate_edits[5]['old_value'])) == int(float(old_work_pref_dict['hourly_rate']))
    assert int(float(candidate_edits[0]['new_value'])) == int(float(new_work_pref_dict['salary']))
    assert int(float(candidate_edits[5]['new_value'])) == int(float(new_work_pref_dict['hourly_rate']))


def test_edit_candidate_email(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's email record
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_email_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['emails'][0]

    # Update Candidate's email
    data = {'candidates': [
        {'id': candidate_id, 'emails': [{'id': old_email_dict['id'], 'address': 'someone@gettalent.com'}]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate
    new_email_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['emails'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_email_dict['address']
    assert candidate_edits[0]['new_value'] == new_email_dict['address']


def test_edit_candidate_phone(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's phone record
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_phone_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['phones'][0]

    # Update Candidate's phone
    data = {'candidates': [
        {'id': candidate_id, 'phones': [{'id': old_phone_dict['id'], 'value': '4084054085'}]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate
    new_email_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['phones'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[1]['old_value'] == old_phone_dict['value']
    assert candidate_edits[1]['new_value'] == new_email_dict['value']


def test_edit_candidate_military_service(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's military service record
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_military_service_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id).\
        json()['candidate']['military_services'][0]

    # Update Candidate's military service
    data = {'candidates': [
        {'id': candidate_id, 'military_services': [{'id': old_military_service_dict['id'], 'branch': 'gettalent'}]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate military services
    new_military_service_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id).\
        json()['candidate']['military_services'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_military_service_dict['branch']
    assert candidate_edits[0]['new_value'] == new_military_service_dict['branch']


def test_edit_candidate_preferred_location_edits(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's preferred location record
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_preferred_location_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id).\
        json()['candidate']['preferred_locations'][0]

    # Update Candidate's preferred location
    data = {'candidates': [
        {'id': candidate_id, 'preferred_locations': [
            {'id': old_preferred_location_dict['id'], 'city': 'man jose'}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate preferred locations
    new_preferred_location_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id).\
        json()['candidate']['preferred_locations'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_preferred_location_dict['city']
    assert candidate_edits[0]['new_value'] == new_preferred_location_dict['city']


def test_edit_candidate_skill_edits(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's skill record
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_skill_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['skills'][0]

    # Update Candidate's skill
    data = {'candidates': [
        {'id': candidate_id, 'skills': [
            {'id': old_skill_dict['id'], 'name': 'useless skill'}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate skills
    new_skill_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['skills'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_skill_dict['name']
    assert candidate_edits[0]['new_value'] == new_skill_dict['name']


def test_edit_candidate_social_network_edits(access_token_first, user_first, talent_pool):
    """
    Test:   Change Candidate's social network record
    Expect: 200
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_sn_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['social_networks'][0]

    # Update Candidate's social network
    data = {'candidates': [
        {'id': candidate_id, 'social_networks': [
            {'id': old_sn_dict['id'], 'name': 'Facebook', 'profile_url': fake.url()}
        ]}
    ]}
    request_to_candidates_resource(access_token_first, 'patch', data)

    # Retrieve Candidate social networks
    new_skill_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['social_networks'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(access_token_first, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_sn_dict['profile_url']
    assert candidate_edits[0]['new_value'] == new_skill_dict['profile_url']
