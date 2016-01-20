"""
Test cases for CandidateResource/post()
"""
# Standard library
import json

# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import Candidate

# Conftest
# from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    check_for_id, AddUserRoles, request_to_candidate_resource, request_to_candidates_resource
)

# Sample data
from candidate_sample_data import (
    generate_single_candidate_data, candidate_educations, candidate_experience,
    candidate_work_preference, candidate_phones, candidate_military_service,
    candidate_preferred_locations, candidate_skills, candidate_social_network,
    complete_candidate_data_for_posting
)
from candidate_service.common.models.candidate import CandidateEmail


class CommonData(object):
    @staticmethod
    def data(talent_pool):
        return {'candidates': [{'emails': [{'address': fake.safe_email()}],
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}


######################## Candidate ########################
def test_create_candidate_without_talent_pools(access_token_first, user_first):
    """
    Test: Attempt to create a candidate without providing talent pool IDs
    Expect: 400
    """
    AddUserRoles.add(user=user_first)
    # Create Candidate
    data = {'candidates': [{'first_name': 'cher'}]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(response=create_resp)
    assert create_resp.status_code == 400 and create_resp.json()['error']['code'] == 3000


def test_create_candidate_successfully(access_token_first, user_first, talent_pool):
    """
    Test:   Create a new candidate and candidate's info
    Expect: 201
    """
    AddUserRoles.add(user=user_first)
    # Create Candidate
    data = {'candidates': [{'first_name': 'joker', 'talent_pool_ids': {'add': [talent_pool.id]}}]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 201


def test_create_candidate_and_retrieve_it(access_token_first, user_first, talent_pool):
    """
    Test:   Create a Candidate and retrieve it. Ensure that the data sent in for creating the
            Candidate is identical to the data obtained from retrieving the Candidate
            minus id-keys
    Expect: 201
    """
    AddUserRoles.add_and_get(user=user_first)
    # Create Candidate
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 200


def test_create_an_existing_candidate(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to recreate an existing Candidate
    Expect: 400
    """
    AddUserRoles.add(user=user_first)

    # Create same Candidate twice
    data = {'candidates': [{'emails': [{'address': fake.safe_email()}],
                            'talent_pool_ids': {'add': [talent_pool.id]}}]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 400
    assert create_resp.json()['error']['code'] == 3013


def test_create_candidate_with_missing_candidates_keys(access_token_first, user_first, talent_pool):
    """
    Test:   Create a Candidate with only first_name provided
    Expect: 400
    """
    AddUserRoles.add(user=user_first)
    # Create Candidate without 'candidate'-key
    data = {'first_name': fake.first_name()}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 400 and create_resp.json()['error']['code'] == 3000


def test_update_candidate_via_post(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to update a Candidate via post()
    Expect: 400
    """
    AddUserRoles.add(user=user_first)
    # Send Candidate object with candidate_id to post
    data = {'candidates': [{'id': 5, 'emails': [{'address': fake.safe_email()}]}]}
    resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(resp)
    assert resp.status_code == 400 and resp.json()['error']['code'] == 3000


def test_create_candidate_with_invalid_fields(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to create a Candidate with bad fields/keys
    Expect: 400
    """
    AddUserRoles.add(user=user_first)
    # Create Candidate with invalid keys/fields
    data = {'candidates': [{'emails': [{'address': 'someone@nice.io'}], 'foo': 'bar',
                            'talent_pool_ids': {'add': [talent_pool.id]}}]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 400 and create_resp.json()['error']['code'] == 3000


def test_create_candidates_in_bulk_with_one_erroneous_data(access_token_first, user_first, talent_pool):
    """
    Test: Attempt to create few candidates, one of which will have bad data
    Expect: 400, no record should be added to the db
    """
    AddUserRoles.add(user=user_first)

    email_1, email_2 = fake.safe_email(), fake.safe_email()
    data = {'candidates': [
        {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_1}]},
        {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_2}]},
        {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': 'bad_email_at_example.com'}]}
    ]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 400 and create_resp.json()['error']['code'] == 3072
    assert CandidateEmail.get_by_address(email_address=email_1) is None
    assert CandidateEmail.get_by_address(email_address=email_2) is None


def test_create_hidden_candidate(access_token_first, user_first, talent_pool):
    """
    Test: Create a candidate that was previously web-hidden
    Expect: 201, candidate should no longer be web hidden.
            No duplicate records should be in the database
    """
    AddUserRoles.all_roles(user=user_first)
    # Create candidate
    create_resp = request_to_candidates_resource(access_token_first, 'post',
                                                 data=CommonData.data(talent_pool))
    candidate_id = create_resp.json()['candidates'][0]['id']
    db.session.commit()
    print response_info(response=create_resp)

    # Retrieve candidate's email
    get_resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    first_can_email = get_resp.json()['candidate']['emails'][0]

    # Delete (hide) candidate
    del_resp = request_to_candidate_resource(access_token_first, 'delete', candidate_id)
    db.session.commit()
    print response_info(response=del_resp)
    candidate = Candidate.get_by_id(candidate_id=candidate_id)
    candidate_emails_count = len(candidate.emails)
    assert del_resp.status_code == 204
    assert candidate.is_web_hidden == 1

    # Create previously deleted candidate
    create_resp = request_to_candidates_resource(access_token_first, 'post',
                                                 data=CommonData.data(talent_pool))
    db.session.commit()
    print response_info(response=create_resp)
    assert create_resp.status_code == 201
    assert candidate.is_web_hidden == 0
    assert CandidateEmail.get_by_address(first_can_email['address']).id == first_can_email['id']
    assert len(candidate.emails) == candidate_emails_count


def test_create_hidden_candidate_with_fields_that_cannot_be_aggregated(access_token_first,
                                                                       user_first, talent_pool):
    """
    Test: Create a candidate that is currently web-hidden
    """
    AddUserRoles.all_roles(user=user_first)

    # Create candidate
    create_resp = request_to_candidates_resource(access_token_first, 'post',
                                                 data=CommonData.data(talent_pool))
    candidate_id = create_resp.json()['candidates'][0]['id']
    db.session.commit()
    print response_info(response=create_resp)

    # Retrieve candidate's first name
    get_resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    candidate_email = get_resp.json()['candidate']['emails'][0]
    full_name = get_resp.json()['candidate']['full_name']

    # Delete candidate
    del_resp = request_to_candidate_resource(access_token_first, 'delete', candidate_id)
    db.session.commit()
    print response_info(response=del_resp)
    candidate = Candidate.get_by_id(candidate_id=candidate_id)
    assert del_resp.status_code == 204
    assert candidate.is_web_hidden == 1

    # Create previously deleted candidate
    data = {'candidates': [{'emails': [{'address': candidate_email['address']}],'first_name': 'McLovin',
                            'talent_pool_ids': {'add': [talent_pool.id]}}]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    db.session.commit()
    print response_info(response=create_resp)
    assert create_resp.status_code == 201
    assert candidate.is_web_hidden == 0

    # Retrieve candidate
    candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    assert candidate_dict['full_name'] != full_name


######################## CandidateAddress ########################
def test_create_candidate_with_bad_zip_code(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to create a Candidate with invalid zip_code
    Expect: 201, but zip_code must be Null
    """
    AddUserRoles.add_and_get(user=user_first)

    # Create Candidate
    data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id])
    data['candidates'][0]['addresses'][0]['zip_code'] = 'ABCDEFG'
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']
    assert candidate_dict['addresses'][0]['zip_code'] is None


######################## CandidateAreaOfInterest ########################
def test_create_candidate_area_of_interest(access_token_first, user_first, talent_pool, domain_aoi):
    """
    Test:   Create CandidateAreaOfInterest
    Expect: 201
    """
    AddUserRoles.add_and_get(user=user_first)

    # Create Candidate + CandidateAreaOfInterest
    data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id], areas_of_interest=domain_aoi)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    print response_info(resp)

    candidate_aoi = resp.json()['candidate']['areas_of_interest']
    assert isinstance(candidate_aoi, list)
    assert candidate_aoi[0]['name'] == AreaOfInterest.query.get(candidate_aoi[0]['id']).name
    assert candidate_aoi[1]['name'] == AreaOfInterest.query.get(candidate_aoi[1]['id']).name


def test_create_candidate_area_of_interest_outside_of_domain(access_token_second, user_second,
                                                             domain_aoi, talent_pool):
    """
    Test: Attempt to create candidate's area of interest outside of user's domain
    Expect: 403
    """
    AddUserRoles.add(user=user_second)
    data = generate_single_candidate_data([talent_pool.id], domain_aoi)
    create_resp = request_to_candidates_resource(access_token_second, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 403 and create_resp.json()['error']['code'] == 3030


######################## CandidateCustomField ########################
def test_create_candidate_custom_fields(access_token_first, user_first, talent_pool,
                                        domain_custom_fields):
    """
    Test:   Create CandidateCustomField
    Expect: 201
    """
    AddUserRoles.add_and_get(user=user_first)

    # Create Candidate + CandidateCustomField
    data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    print response_info(resp)

    can_custom_fields = resp.json()['candidate']['custom_fields']
    assert isinstance(can_custom_fields, list)
    assert can_custom_fields[0]['value'] == data['candidates'][0]['custom_fields'][0]['value']
    assert can_custom_fields[1]['value'] == data['candidates'][0]['custom_fields'][1]['value']


# def test_create_candidate_custom_fields_outside_of_domain(access_token_first, user_first, user_from_diff_domain):
#     """
#     Test: Attempt to create candidate's custom fields outside of user's domain
#     Expect: 403
#     :type user_from_different_domain:    User
#     """
#     AddUserRoles.add(user=user_first)
#
#     data = generate_single_candidate_data(user_from_diff_domain.domain_id)
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 403 and create_resp.json()['error']['code'] == 3040
#
#
# ######################## CandidateEducations ########################
# def test_create_candidate_educations(access_token_first, user_first):
#     """
#     Test:   Create CandidateEducation for Candidate
#     Expect: 201
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate
#     data = candidate_educations()
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     can_educations = candidate_dict['educations']
#     data_educations = data['candidates'][0]['educations'][0]
#     assert isinstance(can_educations, list)
#     assert can_educations[0]['country'] == 'United States'
#     assert can_educations[0]['state'] == data_educations['state']
#     assert can_educations[0]['city'] == data_educations['city']
#     assert can_educations[0]['school_name'] == data_educations['school_name']
#     assert can_educations[0]['school_type'] == data_educations['school_type']
#     assert can_educations[0]['is_current'] == data_educations['is_current']
#
#     can_edu_degrees = can_educations[0]['degrees']
#     assert isinstance(can_edu_degrees, list)
#     assert can_edu_degrees[0]['gpa'] == '3.50'
#     assert can_edu_degrees[0]['start_year'] == str(data_educations['degrees'][0]['start_year'])
#
#     can_edu_degree_bullets = can_edu_degrees[0]['bullets']
#     assert isinstance(can_edu_degree_bullets, list)
#     assert can_edu_degree_bullets[0]['major'] == data_educations['degrees'][0]['bullets'][0]['major']
#
#
# def test_create_candidate_educations_with_no_degrees(access_token_first, user_first):
#     """
#     Test:   Create CandidateEducation for Candidate
#     Expect: 201
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate without degrees
#     data = candidate_educations()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#
#     can_educations = candidate_dict['educations']
#     data_educations = data['candidates'][0]['educations'][0]
#     assert isinstance(can_educations, list)
#     assert can_educations[0]['city'] == data_educations['city']
#     assert can_educations[0]['school_name'] == data_educations['school_name']
#
#     can_edu_degrees = can_educations[0]['degrees']
#     assert isinstance(can_edu_degrees, list)
#
#
# ######################## CandidateExperience ########################
# def test_create_candidate_experience(access_token_first, user_first):
#     """
#     Test:   Create CandidateExperience for Candidate
#     Expect: 201
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate
#     data = candidate_experience()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_experiences = candidate_dict['work_experiences']
#     can_exp_data = data['candidates'][0]['work_experiences'][0]
#     assert isinstance(can_experiences, list)
#
#     assert can_experiences[0]['organization'] == can_exp_data['organization']
#     assert can_experiences[0]['position'] == can_exp_data['position']
#     assert can_experiences[0]['city'] == can_exp_data['city']
#     assert can_experiences[0]['country'] == 'United States'
#     assert can_experiences[0]['is_current'] == can_exp_data['is_current']
#
#     can_exp_bullets = can_experiences[0]['bullets']
#     assert isinstance(can_exp_bullets, list)
#     assert can_exp_bullets[0]['description'] == can_exp_data['bullets'][0]['description']
#
#
# def test_create_candidate_experiences_with_no_bullets(access_token_first, user_first):
#     """
#     Test:   Create CandidateEducation for Candidate
#     Expect: 201
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate without degrees
#     data = {'candidates': [
#         {'work_experiences': [
#             {'organization': 'Apple', 'city': 'Cupertino', 'state': None, 'country': None,
#              'start_month': None, 'start_year': None, 'end_month': None, 'end_year': None,
#              'position': None, 'is_current': None, 'bullets': None}]
#         }
#     ]}
#     data = complete_candidate_data_for_posting(data)
#
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#
#     can_experiences = candidate_dict['work_experiences']
#     assert isinstance(can_experiences, list)
#     assert can_experiences[0]['organization'] == 'Apple'
#     assert can_experiences[0]['city'] == 'Cupertino'
#     can_experience_bullets = can_experiences[0]['bullets']
#     assert isinstance(can_experience_bullets, list)
#
# ######################## CandidateWorkPreference ########################
# def test_create_candidate_work_preference(access_token_first, user_first):
#     """
#     Test:   Create CandidateWorkPreference for Candidate
#     Expect: 201
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate
#     data = candidate_work_preference()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_work_preference = candidate_dict['work_preference']
#     can_work_preference_data = data['candidates'][0]['work_preference']
#     assert isinstance(can_work_preference_data, dict)
#     assert can_work_preference['relocate'] == can_work_preference_data['relocate']
#     assert can_work_preference['travel_percentage'] == can_work_preference_data['travel_percentage']
#     assert can_work_preference['salary'] == can_work_preference_data['salary']
#     assert can_work_preference['employment_type'] == can_work_preference_data['employment_type']
#     assert can_work_preference['third_party'] == can_work_preference_data['third_party']
#     assert can_work_preference['telecommute'] == can_work_preference_data['telecommute']
#     assert can_work_preference['authorization'] == can_work_preference_data['authorization']
#
# ######################## CandidateEmails ########################
# def test_create_candidate_without_email(access_token_first, user_first):
#     """
#     Test:   Attempt to create a Candidate with no email
#     Expect: 201
#     """
#
#     # Create Candidate with no email
#     AddUserRoles.add_and_get(user=user_first)
#     data = {'candidates': [{'first_name': 'john', 'last_name': 'stark'}]}
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Create Candidate
#     # add_role_to_test_user(access_token_first, user_first, ['CAN_ADD_CANDIDATES']) with empty email-list
#     data = {'candidates': [{'first_name': 'john', 'last_name': 'stark', 'emails': [{}]}]}
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 400 and create_resp.json()['error']['code'] == 3000
#
#
# def test_create_candidate_with_bad_email(access_token_first, user_first):
#     """
#     Test:   Attempt to create a Candidate with invalid email format
#     Expect: 400
#     """
#     AddUserRoles.add(user=user_first)
#
#     # Create Candidate
#     data = {'candidates': [{'emails': [{'label': None, 'is_default': True, 'address': 'bad_email.com'}]}]}
#     data = complete_candidate_data_for_posting(data)
#
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 400 and create_resp.json()['error']['code'] == 3072
#
#
# def test_create_candidate_without_email_label(access_token_first, user_first):
#     """
#     Test:   Create a Candidate without providing email's label
#     Expect: 201, email's label must be 'Primary'
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate without email-label
#     data = {'candidates': [
#         {'emails': [
#             {'label': None, 'is_default': None, 'address': fake.safe_email()},
#             {'label': None, 'is_default': None, 'address': fake.safe_email()}
#         ]}
#     ]}
#
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#
#     assert create_resp.status_code == 201
#     assert candidate_dict['emails'][0]['label'] == 'Primary'
#     assert candidate_dict['emails'][-1]['label'] == 'Other'
#
#
# ######################## CandidatePhones ########################
# def test_create_candidate_phones(access_token_first, user_first):
#     """
#     Test:   Create CandidatePhones for Candidate
#     Expect: 201
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate
#     data = candidate_phones()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_phones = candidate_dict['phones']
#     can_phones_data = data['candidates'][0]['phones']
#     assert isinstance(can_phones, list)
#     assert can_phones[0]['label'] == can_phones_data[0]['label'].capitalize()
#
#
# def test_create_candidate_without_phone_label(access_token_first, user_first):
#     """
#     Test:   Create a Candidate without providing phone's label
#     Expect: 201, phone's label must be 'Primary'
#     """
#     AddUserRoles.add_and_get(user=user_first)
#
#     # Create Candidate without label
#     data = {'candidates': [{'phones':
#         [
#             {'label': None, 'is_default': None, 'value': '6504084069'},
#             {'label': None, 'is_default': None, 'value': '6504084069'}
#         ]}
#     ]}
#     data = complete_candidate_data_for_posting(data)
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#
#     assert create_resp.status_code == 201
#     assert candidate_dict['phones'][0]['label'] == 'Home'
#     assert candidate_dict['phones'][-1]['label'] == 'Other'
#
#
# def test_create_candidate_with_bad_phone_label(access_token_first, user_first):
#     """
#     Test:   e.g. Phone label = 'vork'
#     Expect: 201, phone label must be 'Other'
#     """
#
#     # Create Candidate without label
#     AddUserRoles.add_and_get(user=user_first)
#     data = {'candidates': [{'phones':
#         [
#             {'label': 'vork', 'is_default': None, 'value': '6504084069'},
#             {'label': '2564', 'is_default': None, 'value': '6504084069'}
#         ]}
#     ]}
#     data = complete_candidate_data_for_posting(data)
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#
#     assert create_resp.status_code == 201
#     assert candidate_dict['phones'][0]['label'] == 'Other'
#     assert candidate_dict['phones'][-1]['label'] == 'Other'
#
#
# ######################## CandidateMilitaryService ########################
# def test_create_candidate_military_service(access_token_first, user_first):
#     """
#     Test:   Create CandidateMilitaryService for Candidate
#     Expect: 201
#     """
#
#     # Create Candidate
#     AddUserRoles.add_and_get(user=user_first)
#     data = candidate_military_service()
#     create_resp = request_to_candidates_resource(access_token_first, 'post', data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_military_services = candidate_dict['military_services']
#     can_military_services_data = data['candidates'][0]['military_services'][0]
#     assert isinstance(can_military_services, list)
#     assert can_military_services[-1]['comments'] == can_military_services_data['comments']
#     assert can_military_services[-1]['highest_rank'] == can_military_services_data['highest_rank']
#     assert can_military_services[-1]['branch'] == can_military_services_data['branch']
#
#
# ######################## CandidatePreferredLocations ########################
# def test_create_candidate_preferred_location(access_token_first, user_first):
#     """
#     Test:   Create CandidatePreferredLocations for Candidate
#     Expect: 201
#     """
#
#     # Create Candidate
#     AddUserRoles.add_and_get(user=user_first)
#     data = candidate_preferred_locations()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_preferred_locations = candidate_dict['preferred_locations']
#     can_preferred_locations_data = data['candidates'][0]['preferred_locations']
#     assert isinstance(can_preferred_locations, list)
#     assert can_preferred_locations[0]['city'] == can_preferred_locations_data[0]['city']
#     assert can_preferred_locations[0]['city'] == can_preferred_locations_data[0]['city']
#     assert can_preferred_locations[0]['state'] == can_preferred_locations_data[0]['state']
#
#
# ######################## CandidateSkills ########################
# def test_create_candidate_skills(access_token_first, user_first):
#     """
#     Test:   Create CandidateSkill for Candidate
#     Expect: 201
#     """
#
#     # Create Candidate
#     AddUserRoles.add_and_get(user=user_first)
#     data = candidate_skills()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_skills = candidate_dict['skills']
#     can_skills_data = data['candidates'][0]['skills'][0]
#     assert isinstance(can_skills, list)
#     assert can_skills[0]['name'] == can_skills_data['name']
#     assert can_skills[0]['months_used'] == can_skills_data['months_used']
#     assert can_skills[0]['name'] == can_skills_data['name']
#     assert can_skills[0]['months_used'] == can_skills_data['months_used']
#
#
# ######################## CandidateSocialNetworks ########################
# def test_create_candidate_social_networks(access_token_first, user_first):
#     """
#     Test:   Create CandidateSocialNetwork for Candidate
#     Expect: 201
#     """
#
#     # Create Candidate
#     AddUserRoles.add_and_get(user=user_first)
#     data = candidate_social_network()
#     create_resp = post_to_candidate_resource(token, data=data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 201
#
#     # Retrieve Candidate
#     candidate_id = create_resp.json()['candidates'][0]['id']
#     candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
#     assert check_for_id(_dict=candidate_dict) is not False
#
#     # Assert data sent in = data retrieved
#     can_social_networks = candidate_dict['social_networks']
#     can_social_networks_data = data['candidates'][0]['social_networks']
#     assert isinstance(can_social_networks, list)
#     assert can_social_networks[0]['name'] == 'Facebook'
#     assert can_social_networks[0]['profile_url'] == can_social_networks_data[0]['profile_url']
#     assert can_social_networks[1]['name'] == 'Twitter'
#     assert can_social_networks[1]['profile_url'] == can_social_networks_data[1]['profile_url']
#
# # TODO: test for erroneous data sent in; e.g. name=foo, profile_url='profile.com'