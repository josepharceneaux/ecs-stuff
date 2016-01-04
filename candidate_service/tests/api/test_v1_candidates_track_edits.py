"""
Test cases for keeping track of changes made to a Candidate
"""
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
    patch_to_candidate_resource, request_to_candidate_edit_resource
)


def test_edit_candidate_primary_info(sample_user, user_auth):
    """
    Test:   Change Candidate's first and last names
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
    old_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    # Update Candidate's first and last names
    data = {'candidates': [
        {'id': candidate_id, 'first_name': 'bruce', 'last_name': 'willis'}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    new_candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200


def test_edit_candidate_address(sample_user, user_auth):
    """
    Test:   Edit Candidate's address
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
    old_address_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['addresses'][0]

    # Update Candidate's address
    data = {'candidates': [
        {'id': candidate_id, 'addresses': [
            {'id': old_address_dict['id'], 'address_line_1': '255 west santa clara'}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate addresses
    new_address_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['addresses'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_address_dict['address_line_1'] != old_address_dict['address_line_1']
    assert candidate_edits[0]['old_value'] == old_address_dict['address_line_1']
    assert candidate_edits[0]['new_value'] == new_address_dict['address_line_1']


def test_edit_candidate_custom_field(sample_user, user_auth):
    """
    Test:   Change Candidate's custom fields
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_custom_field_dict = get_from_candidate_resource(token, candidate_id)\
        .json()['candidate']['custom_fields'][0]
    db.session.commit()

    # Update Candidate's custom field
    data = {'candidates': [
        {'id': candidate_id, 'custom_fields': [
            {'id': old_custom_field_dict['id'], 'value': 'foobar'}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate custom fields
    new_custom_field_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['custom_fields'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_custom_field_dict['value']
    assert candidate_edits[0]['new_value'] == new_custom_field_dict['value']


def test_edit_candidate_education(sample_user, user_auth):
    """
    Test:   Change Candidate's education records
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_education_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations'][0]

    # Update Candidate's education
    data = {'candidates': [
        {'id': candidate_id, 'educations': [
            {'id': old_education_dict['id'], 'school_name': 'UC Davis'}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate educations
    new_education_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_education_dict['school_name'] != old_education_dict['school_name']
    assert candidate_edits[0]['old_value'] == old_education_dict['school_name']
    assert candidate_edits[0]['new_value'] == new_education_dict['school_name']


def test_edit_candidate_education_degree(sample_user, user_auth):
    """
    Test:   Change Candidate's education degree records
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_education_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations'][0]

    # Update Candidate's education degree
    data = {'candidates': [
        {'id': candidate_id, 'educations': [
            {'id': old_education_dict['id'], 'degrees': [
                {'id': old_education_dict['degrees'][0]['id'], 'type': 'MS', 'title': 'Biomedical Engineering'}
            ]}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate education
    new_education_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_education_dict['degrees'][0]['type'] != old_education_dict['degrees'][0]['type']
    assert new_education_dict['degrees'][0]['title'] != old_education_dict['degrees'][0]['title']
    assert candidate_edits[0]['old_value'] == old_education_dict['degrees'][0]['type']
    assert candidate_edits[0]['new_value'] == new_education_dict['degrees'][0]['type']
    assert candidate_edits[1]['old_value'] == old_education_dict['degrees'][0]['title']
    assert candidate_edits[1]['new_value'] == new_education_dict['degrees'][0]['title']


def test_edit_candidate_education_degree_bullet(sample_user, user_auth):
    """
    Test:   Change Candidate's education degree bullet records
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    old_education_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations'][0]
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
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate education
    new_education_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations'][0]
    new_degree_bullet_dict = new_education_dict['degrees'][0]['bullets'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_degree_bullet_dict['major'] != old_degree_bullet_dict['major']
    assert candidate_edits[0]['old_value'] == old_degree_bullet_dict['major']
    assert candidate_edits[0]['new_value'] == new_degree_bullet_dict['major']


def test_edit_candidate_experience(sample_user, user_auth):
    """
    Test:   Change Candidate's experience records
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
    old_experience_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_experiences'][0]

    # Update Candidate's experience
    data = {'candidates': [
        {'id': candidate_id, 'work_experiences': [
            {'id': old_experience_dict['id'], 'organization': 'Dice', 'position': 'Software Engineer'}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    new_experience_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_experiences'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert new_experience_dict['organization'] != old_experience_dict['organization']
    assert new_experience_dict['position'] != old_experience_dict['position']
    assert candidate_edits[0]['old_value'] == old_experience_dict['position']
    assert candidate_edits[0]['new_value'] == new_experience_dict['position']
    assert candidate_edits[1]['old_value'] == old_experience_dict['organization']
    assert candidate_edits[1]['new_value'] == new_experience_dict['organization']


def test_edit_candidate_experience_bullet(sample_user, user_auth):
    """
    Test:   Change Candidate's experience bullet records
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
    old_experience_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_experiences'][0]
    old_experience_bullet_dict = old_experience_dict['bullets'][0]

    # Update Candidate's experience bullet
    data = {'candidates': [
        {'id': candidate_id, 'work_experiences': [
            {'id': old_experience_dict['id'], 'bullets': [
                {'id': old_experience_bullet_dict['id'], 'description': 'job sucked'}
            ]}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    new_experience_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_experiences'][0]
    new_experience_bullet_dict = new_experience_dict['bullets'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_experience_bullet_dict['description']
    assert candidate_edits[0]['new_value'] == new_experience_bullet_dict['description']


def test_edit_candidate_work_preference(sample_user, user_auth):
    """
    Test:   Change Candidate's work preference records
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
    old_work_pref_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_preference']

    # Update Candidate's work preference
    data = {'candidates': [
        {'id': candidate_id, 'work_preference': {
            'id': old_work_pref_dict['id'], 'salary': '150000', 'hourly_rate': '75'
        }}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    new_work_pref_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['work_preference']

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == int(old_work_pref_dict['salary']).__str__()
    assert candidate_edits[5]['old_value'] == old_work_pref_dict['hourly_rate'].__str__()
    assert candidate_edits[0]['new_value'] == int(new_work_pref_dict['salary']).__str__()
    assert candidate_edits[5]['new_value'] == int(new_work_pref_dict['hourly_rate']).__str__()


def test_edit_candidate_email(sample_user, user_auth):
    """
    Test:   Change Candidate's email record
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
    old_email_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails'][0]

    # Update Candidate's email
    data = {'candidates': [
        {'id': candidate_id, 'emails': [{'id': old_email_dict['id'], 'address': 'someone@gettalent.com'}]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    new_email_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_email_dict['address']
    assert candidate_edits[0]['new_value'] == new_email_dict['address']


def test_edit_candidate_phone(sample_user, user_auth):
    """
    Test:   Change Candidate's phone record
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
    old_phone_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones'][0]

    # Update Candidate's phone
    data = {'candidates': [
        {'id': candidate_id, 'phones': [{'id': old_phone_dict['id'], 'value': '4084054085'}]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate
    new_email_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['phones'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[1]['old_value'] == old_phone_dict['value']
    assert candidate_edits[1]['new_value'] == new_email_dict['value']


def test_edit_candidate_military_service(sample_user, user_auth):
    """
    Test:   Change Candidate's military service record
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
    old_military_service_dict = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services'][0]

    # Update Candidate's military service
    data = {'candidates': [
        {'id': candidate_id, 'military_services': [{'id': old_military_service_dict['id'], 'branch': 'gettalent'}]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate military services
    new_military_service_dict = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['military_services'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_military_service_dict['branch']
    assert candidate_edits[0]['new_value'] == new_military_service_dict['branch']


def test_edit_candidate_preferred_location_edits(sample_user, user_auth):
    """
    Test:   Change Candidate's preferred location record
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
    old_preferred_location_dict = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations'][0]

    # Update Candidate's preferred location
    data = {'candidates': [
        {'id': candidate_id, 'preferred_locations': [
            {'id': old_preferred_location_dict['id'], 'city': 'man jose'}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate preferred locations
    new_preferred_location_dict = get_from_candidate_resource(token, candidate_id).\
        json()['candidate']['preferred_locations'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_preferred_location_dict['city']
    assert candidate_edits[0]['new_value'] == new_preferred_location_dict['city']


def test_edit_candidate_skill_edits(sample_user, user_auth):
    """
    Test:   Change Candidate's skill record
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
    old_skill_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['skills'][0]

    # Update Candidate's skill
    data = {'candidates': [
        {'id': candidate_id, 'skills': [
            {'id': old_skill_dict['id'], 'name': 'useless skill'}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate skills
    new_skill_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['skills'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_skill_dict['name']
    assert candidate_edits[0]['new_value'] == new_skill_dict['name']


def test_edit_candidate_social_network_edits(sample_user, user_auth):
    """
    Test:   Change Candidate's social network record
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
    old_sn_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['social_networks'][0]

    # Update Candidate's social network
    data = {'candidates': [
        {'id': candidate_id, 'social_networks': [
            {'id': old_sn_dict['id'], 'name': 'Facebook', 'profile_url': fake.url()}
        ]}
    ]}
    patch_to_candidate_resource(token, data)

    # Retrieve Candidate social networks
    new_skill_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']['social_networks'][0]

    # Retrieve Candidate Edits
    edit_resp = request_to_candidate_edit_resource(token, 'get', candidate_id)
    print response_info(edit_resp)

    candidate_edits = edit_resp.json()['candidate']['edits']
    assert edit_resp.status_code == 200
    assert candidate_edits[0]['old_value'] == old_sn_dict['profile_url']
    assert candidate_edits[0]['new_value'] == new_skill_dict['profile_url']

