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
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    create_same_candidate, check_for_id
)

# Sample data
from candidate_sample_data import (
    generate_single_candidate_data, candidate_educations, candidate_experience,
    candidate_work_preference, candidate_phones, candidate_military_service,
    candidate_preferred_locations, candidate_skills, candidate_social_network,
    candidate_areas_of_interest, candidate_custom_fields
)

# TODO: Implement server side custom error codes and add necessary assertions
######################## Candidate ########################
def test_create_candidate_successfully(sample_user, user_auth):
    """
    Test:   Create a new candidate and candidate's info
    Expect: 201
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    resp_dict = create_resp.json()
    print response_info(create_resp)
    assert create_resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


def test_schema_validation(sample_user, user_auth):
    """
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    data = {'candidates': [
        {
            'emails': [{'label': None, 'address': fake.safe_email(), 'is_default': True}],
            'first_name': 'john', 'middle_name': '', 'last_name': '', 'addresses': [],
            'social_networks': [], 'skills': [], 'work_experiences': [], #'work_preference': {},
            'educations': [], 'custom_fields': [], 'preferred_locations': [], 'military_services': [],
            'areas_of_interest': [], 'phones': []
        }
    ]}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)


def test_create_candidate_and_retrieve_it(sample_user, user_auth):
    """
    Test:   Create a Candidate and retrieve it. Ensure that the data sent in for creating the
            Candidate is identical to the data obtained from retrieving the Candidate
            minus id-keys
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    data = generate_single_candidate_data()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = get_from_candidate_resource(token, candidate_id)
    print response_info(resp)


def test_create_an_existing_candidate(sample_user, user_auth):
    """
    Test:   Attempt to recreate an existing Candidate
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create same Candidate twice
    create_resp = create_same_candidate(token)

    resp_dict = create_resp.json()
    print response_info(create_resp)
    assert create_resp.status_code == 400
    assert 'error' in resp_dict # TODO: assert on server side custom errors


def test_create_candidate_with_missing_keys(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with missing key(s)
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate without 'candidate'-key
    data = generate_single_candidate_data()['candidate']
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)
    assert create_resp.status_code == 400


def test_update_candidate_via_post(sample_user, user_auth):
    """
    Test:   Attempt to update a Candidate via post()
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()

    # Send Candidate object with candidate_id to post
    resp = post_to_candidate_resource(token, data=candidate_dict)
    print response_info(resp)
    assert resp.status_code == 400

# TODO complete test once input validation is utilized
# def test_create_candidate_with_invalid_fields(sample_user, user_auth):
#     """
#     Test:   Attempt to create a Candidate with bad fields/keys
#     Expect: 400
#     :type sample_user:  User
#     :type user_auth:    UserAuthentication
#     """
#     # Get access token
#     token = user_auth.get_auth_token(sample_user, True)['access_token']
#
#     # Create Candidate with invalid keys/fields
#     data = {'candidates': [{'emails': [{'address': 'someone@nice.io'}], 'foo': 'bar'}]}
#     create_resp = post_to_candidate_resource(token, data)
#     print response_info(create_resp)
#     assert create_resp.status_code == 400


######################## CandidateAddress ########################
def test_create_candidate_with_bad_zip_code(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with invalid zip_code
    Expect: 201, but zip_code must be Null
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = {'candidate': {'emails': [{'address': 'some@nice.com'}], 'addresses': [
        {'address_line_1': '225 west santa flara', 'zip_code': 'ABCDEFG'}
    ]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert candidate_dict['addresses'][0]['zip_code'] == None


######################## CandidateAreaOfInterest ########################
def test_create_candidate_area_of_interest(sample_user, user_auth):
    """
    Test:   Create CandidateAreaOfInterest
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate + CandidateAreaOfInterest
    data = candidate_areas_of_interest(domain_id=sample_user.domain_id)
    create_resp = post_to_candidate_resource(access_token=token, data=data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = get_from_candidate_resource(token, candidate_id)
    print response_info(resp)

    candidate_aoi = resp.json()['candidate']['areas_of_interest']
    assert isinstance(candidate_aoi, list)
    assert candidate_aoi[0]['name'] == db.session.query(AreaOfInterest).get(candidate_aoi[0]['id']).name
    assert candidate_aoi[1]['name'] == db.session.query(AreaOfInterest).get(candidate_aoi[1]['id']).name

######################## CandidateCustomField ########################
def test_create_candidate_custom_fields(sample_user, user_auth):
    """
    Test:   Create CandidateCustomField
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate + CandidateCustomField
    data = candidate_custom_fields(domain_id=sample_user.domain_id)
    create_resp = post_to_candidate_resource(access_token=token, data=data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = get_from_candidate_resource(token, candidate_id)
    print response_info(resp)

    can_custom_fields = resp.json()['candidate']['custom_fields']
    assert isinstance(can_custom_fields, list)
    assert can_custom_fields[0]['value'] == data['candidate']['custom_fields'][0]['value']
    assert can_custom_fields[1]['value'] == data['candidate']['custom_fields'][1]['value']

######################## CandidateEducations ########################
def test_create_candidate_educations(sample_user, user_auth):
    """
    Test:   Create CandidateEducation for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, data=candidate_educations())
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    can_educations = candidate_dict['educations']
    assert isinstance(can_educations, list)
    assert can_educations[0]['country'] == 'United States'
    assert can_educations[0]['state'] == 'ca'
    assert can_educations[0]['city'] == 'palo alto'
    assert can_educations[0]['school_name'] == 'stanford'
    assert can_educations[0]['school_type'] == 'university'
    assert can_educations[0]['is_current'] == False

    can_edu_degrees = can_educations[0]['degrees']
    assert isinstance(can_edu_degrees, list)
    assert can_edu_degrees[0]['gpa'] == '1.50'
    assert can_edu_degrees[0]['start_year'] == '2002'

    can_edu_degree_bullets = can_edu_degrees[0]['bullets']
    assert isinstance(can_edu_degree_bullets, list)
    assert can_edu_degree_bullets[0]['major'] == 'mathematics'


def test_create_candidate_educations_with_no_degrees(sample_user, user_auth):
    """
    Test:   Create CandidateEducation for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate without degrees
    data = {'candidate': {'emails': [{'address': fake.email()}], 'educations': [
        {'school_name': 'SJSU', 'city': 'San Jose', 'degrees': None}
    ]}}
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    can_educations = candidate_dict['educations']
    assert isinstance(can_educations, list)
    assert can_educations[0]['city'] == 'San Jose'
    assert can_educations[0]['school_name'] == 'SJSU'

    can_edu_degrees = can_educations[0]['degrees']
    assert isinstance(can_edu_degrees, list)


######################## CandidateExperience ########################
def test_create_cand_experience(sample_user, user_auth):
    """
    Test:   Create CandidateExperience for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_experience()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_experiences = candidate_dict['work_experiences']
    can_exp_data = data['candidate']['work_experiences'][0]
    assert isinstance(can_experiences, list)

    assert can_experiences[0]['organization'] == can_exp_data['organization']
    assert can_experiences[0]['position'] == can_exp_data['position']
    assert can_experiences[0]['city'] == can_exp_data['city']
    assert can_experiences[0]['country'] == 'United States'
    assert can_experiences[0]['is_current'] == can_exp_data['is_current']

    can_exp_bullets = can_experiences[0]['bullets']
    assert isinstance(can_exp_bullets, list)
    assert can_exp_bullets[0]['description'] == can_exp_data['bullets'][0]['description']


def test_create_candidate_experiences_with_no_bullets(sample_user, user_auth):
    """
    Test:   Create CandidateEducation for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate without degrees
    data = {'candidate': {'emails': [{'address': fake.email()}], 'work_experiences': [
        {'organization': 'Apple', 'city': 'Cupertino', 'bullets': None}
    ]}}
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    can_experiences = candidate_dict['work_experiences']
    assert isinstance(can_experiences, list)
    assert can_experiences[0]['organization'] == 'Apple'
    assert can_experiences[0]['city'] == 'Cupertino'
    can_experience_bullets = can_experiences[0]['bullets']
    assert isinstance(can_experience_bullets, list)

######################## CandidateWorkPreference ########################
def test_create_candidate_work_preference(sample_user, user_auth):
    """
    Test:   Create CandidateWorkPreference for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_work_preference()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_work_preference = candidate_dict['work_preference']
    can_work_preference_data = data['candidate']['work_preference']
    print "can_work_preference_data = %s" % can_work_preference_data
    assert isinstance(can_work_preference_data, dict)
    assert can_work_preference['relocate'] == can_work_preference_data['relocate']
    assert can_work_preference['travel_percentage'] == can_work_preference_data['travel_percentage']
    assert can_work_preference['salary'] == can_work_preference_data['salary']
    assert can_work_preference['employment_type'] == can_work_preference_data['employment_type']
    assert can_work_preference['third_party'] == can_work_preference_data['third_party']
    assert can_work_preference['telecommute'] == can_work_preference_data['telecommute']
    assert can_work_preference['authorization'] == can_work_preference_data['authorization']
    assert can_work_preference['hourly_rate'] == json.loads(can_work_preference_data['hourly_rate'])

######################## CandidateEmails ########################
def test_create_candidate_without_email(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with no email
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate with no email-object
    data = {'candidate': {'first_name': 'john', 'last_name': 'stark'}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)
    assert create_resp.status_code == 400

    # Create Candidate with empty email-list
    data = {'candidate': {'first_name': 'john', 'last_name': 'stark', 'emails': [{}]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)
    assert create_resp.status_code == 400


def test_create_candidate_with_bad_email(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with invalid email format
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = {'candidate': {'first_name': 'john', 'emails': [{'address': 'bad_email.com'}]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)

    assert create_resp.status_code == 400


def test_create_candidate_without_email_label(sample_user, user_auth):
    """
    Test:   Create a Candidate without providing email's label
    Expect: 201, email's label must be 'Primary'
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate without email-label
    data = {'candidate': {'emails': [{'address': fake.email()}, {'address': fake.email()}]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert create_resp.status_code == 201
    assert candidate_dict['emails'][0]['label'] == 'Primary'
    assert candidate_dict['emails'][-1]['label'] == 'Other'


######################## CandidatePhones ########################
def test_create_candidate_phones(sample_user, user_auth):
    """
    Test:   Create CandidatePhones for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_phones()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_phones = candidate_dict['phones']
    can_phones_data = data['candidate']['phones']
    assert isinstance(can_phones, list)
    assert can_phones[0]['label'] == can_phones_data[0]['label'].capitalize()


def test_create_candidate_without_phone_label(sample_user, user_auth):
    """
    Test:   Create a Candidate without providing phone's label
    Expect: 201, phone's label must be 'Primary'
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate without phone-label
    data = {'candidate': {'emails': [{'address': fake.email()}], 'phones': [
        {'value': '6504084069'}, {'value': '6509554065'}
    ]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert create_resp.status_code == 201
    assert candidate_dict['phones'][0]['label'] == 'Home'
    assert candidate_dict['phones'][-1]['label'] == 'Other'

# TODO: test with invalid phone numbers, bad lables, e.g. label: vork, number: sdgfka

######################## CandidateMilitaryService ########################
def test_create_candidate_military_service(sample_user, user_auth):
    """
    Test:   Create CandidateMilitaryService for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_military_service()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_military_services = candidate_dict['military_services']
    can_military_services_data = data['candidate']['military_services'][0]
    assert isinstance(can_military_services, list)
    # assert can_military_services[0]['country'] == can_military_services_data['country'].capitalize()
    assert can_military_services[0]['comments'] == can_military_services_data['comments']
    assert can_military_services[0]['highest_rank'] == can_military_services_data['highest_rank']
    assert can_military_services[0]['branch'] == can_military_services_data['branch']
#TODO: test for from_date and to_date

######################## CandidatePreferredLocations ########################
def test_create_candidate_preferred_location(sample_user, user_auth):
    """
    Test:   Create CandidatePreferredLocations for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_preferred_locations()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_preferred_locations = candidate_dict['preferred_locations']
    can_preferred_locations_data = data['candidate']['preferred_locations']
    assert isinstance(can_preferred_locations, list)
    assert can_preferred_locations[0]['address'] == can_preferred_locations_data[0]['address']
    assert can_preferred_locations[0]['city'] == can_preferred_locations_data[0]['city']
    assert can_preferred_locations[0]['city'] == can_preferred_locations_data[0]['city']
    assert can_preferred_locations[0]['state'] == can_preferred_locations_data[0]['state']
    # assert can_preferred_locations[0]['country'] == 'Albania'


######################## CandidateSkills ########################
def test_create_candidate_skills(sample_user, user_auth):
    """
    Test:   Create CandidateSkill for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_skills()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_skills = candidate_dict['skills']
    can_skills_data = data['candidate']['skills'][0]
    assert isinstance(can_skills, list)
    assert can_skills[0]['name'] == can_skills_data['name']
    assert can_skills[0]['months_used'] == can_skills_data['months_used']
    assert can_skills[0]['name'] == can_skills_data['name']
    assert can_skills[0]['months_used'] == can_skills_data['months_used']
# TODO: test for last_used; i.e. what date object?

######################## CandidateSocialNetworks ########################
def test_create_candidate_social_networks(sample_user, user_auth):
    """
    Test:   Create CandidateSocialNetwork for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_social_network()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_social_networks = candidate_dict['social_networks']
    can_social_networks_data = data['candidate']['social_networks']
    assert isinstance(can_social_networks, list)
    assert can_social_networks[0]['name'] == 'LinkedIn'
    assert can_social_networks[0]['profile_url'] == can_social_networks_data[0]['profile_url']
    assert can_social_networks[1]['name'] == 'Google+'
    assert can_social_networks[1]['profile_url'] == can_social_networks_data[1]['profile_url']

# TODO: test for erroneous data sent in; e.g. name=foo, profile_url='profile.com'