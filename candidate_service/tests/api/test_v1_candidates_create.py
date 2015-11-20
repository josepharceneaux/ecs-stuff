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
    generate_single_candidate_data, candidate_educations, candidate_work_experience,
    candidate_work_preference
)

# TODO: Implement server side custom error codes and add necessary assertions
######################## Candidate ########################
def test_create_candidate(sample_user, user_auth):
    """
    Test:   Create a new candidate and candidate's info
    Expect: 201
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    resp_dict = create_resp.json()
    print response_info(create_resp.request, resp_dict, create_resp.status_code)
    assert create_resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


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
    print "data = %s" % data
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)

    # Retreive Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id)
    # TODO: get-object must be identical to data after removing all ids & none values


def test_create_an_existing_candidate(sample_user, user_auth):
    """
    Test:   Attempt to recreate an existing Candidate
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create same Candidate twice
    create_resp = create_same_candidate(token)

    resp_dict = create_resp.json()
    print response_info(create_resp.request, resp_dict, create_resp.status_code)
    assert create_resp.status_code == 400
    assert 'error' in resp_dict


def test_create_candidate_without_email(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with no email
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate with no email-object
    data = {'candidate': {'first_name': 'john', 'last_name': 'stark'}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
    assert create_resp.status_code == 400

    # Create Candidate with empty email-list
    data = {'candidate': {'first_name': 'john', 'last_name': 'stark', 'emails': [{}]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
    assert create_resp.status_code == 400


def test_create_candidate_with_bad_email(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with invalid email format
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = {'candidate': {'first_name': 'john', 'emails': [{'address': 'bad_email.com'}]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)

    assert create_resp.status_code == 400


def test_create_candidate_with_missing_keys(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with missing key(s)
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate without 'candidate'-key
    data = generate_single_candidate_data()['candidate']
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)

    assert create_resp.status_code == 400


def test_update_candidate_via_post(sample_user, user_auth):
    """
    Test:   Attempt to update a Candidate via post()
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()

    # Send Candidate object with candidate_id to post
    resp = post_to_candidate_resource(token, data=candidate_dict)
    print response_info(resp.request, resp.json(), resp.status_code)

    assert resp.status_code == 400

######################## CandidateAddress ########################
def test_create_candidate_with_bad_zip_code(sample_user, user_auth):
    """
    Test:   Attempt to create a Candidate with invalid zip_code
    Expect: 201, but zip_code must be Null
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = {'candidate': {'emails': [{'address': 'some@nice.com'}], 'addresses': [
        {'address_line_1': '225 west santa flara', 'zip_code': 'ABCDEFG'}
    ]}}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert candidate_dict['addresses'][0]['zip_code'] == None

######################## CandidateAreaOfInterest ########################
# TODO: create test once user service is available

######################## CandidateCustomFields ########################
# TODO: create test once user service is available

######################## CandidateEducations ########################
def test_create_candidate_educations(sample_user, user_auth):
    """
    Test:   Create CandidateEducation for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, data=candidate_educations())
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
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

    can_edu_degree_bullets = can_edu_degrees[0]['degree_bullets']
    assert isinstance(can_edu_degree_bullets, list)
    assert can_edu_degree_bullets[0]['major'] == 'mathematics'

######################## CandidateExperience ########################
def test_create_candidate_work_experience(sample_user, user_auth):
    """
    Test:   Create CandidateEducation for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_work_experience()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_experience = candidate_dict['work_experiences']
    can_exp_data = data['candidate']['work_experiences'][0]
    assert isinstance(can_experience, list)
    assert can_experience[0]['company'] == can_exp_data['organization']
    assert can_experience[0]['role'] == can_exp_data['position']
    assert can_experience[0]['city'] == can_exp_data['city']
    assert can_experience[0]['country'] == 'United States'
    assert can_experience[0]['is_current'] == can_exp_data['is_current']

    can_exp_bullets = can_experience[0]['experience_bullets']
    assert isinstance(can_exp_bullets, list)
    assert can_exp_bullets[0]['description'] == can_exp_data['experience_bullets'][0]['description']

######################## CandidateWorkPreference ########################
def test_create_candidate_work_preference(sample_user, user_auth):
    """
    Test:   Create CandidateEducation for Candidate
    Expect: 201
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token
    token = user_auth.get_auth_token(sample_user, get_bearer_token=True)['access_token']

    # Create Candidate
    data = candidate_work_preference()
    create_resp = post_to_candidate_resource(token, data=data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    assert check_for_id(_dict=candidate_dict) is not False

    # Assert data sent in = data retrieved
    can_work_preference = candidate_dict['work_preference']
    can_work_preference_data = data['candidate']['work_preference']
    assert isinstance(can_work_preference_data, dict)
    assert can_work_preference['relocate'] == can_work_preference_data['relocate']
    assert can_work_preference['travel_percentage'] == can_work_preference_data['travel_percentage']
    assert can_work_preference['salary'] == can_work_preference_data['salary']
    assert can_work_preference['tax_terms'] == can_work_preference_data['tax_terms']
    assert can_work_preference['third_party'] == can_work_preference_data['third_party']
    assert can_work_preference['telecommute'] == can_work_preference_data['telecommute']
    assert can_work_preference['authorization'] == can_work_preference_data['authorization']
    assert can_work_preference['hourly_rate'] == json.loads(can_work_preference_data['hourly_rate'])


######################## CandidateEmails ########################
######################## CandidatePhones ########################
######################## CandidateMilitaryService ########################
######################## CandidatePreferredLocations ########################
######################## CandidateSkills ########################
######################## CandidateSocialNetworks ########################