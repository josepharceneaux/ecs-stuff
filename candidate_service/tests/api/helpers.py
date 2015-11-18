"""
Helper functions for tests pertaining to candidate_service's restful services
"""
# Standard library
import requests
import json

# Candidate's sample data
from candidate_service.common.tests.sample_data import (
    generate_single_candidate_data, candidate_data_for_update
)


class CandidateResourceUrl():
    def __init__(self):
        pass

    BASE_URL = "http://127.0.0.1:8005/v1/candidates"


def response_info(resp_request, resp_json, resp_status):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    :type resp_json:        dict
    :type resp_status:      int
    """
    args = (resp_request, resp_json, resp_status)
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % args


def post_to_candidate_resource(access_token, data=None):
    """
    Function sends a post request to CandidateResource,
    i.e. CandidateResource/post()
    """
    if not data:
        data = generate_single_candidate_data()

    resp = requests.post(
        url=CandidateResourceUrl.BASE_URL,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp


def create_same_candidate(access_token):
    """
    Function will attempt to create the same Candidate twice
    """
    # Create Candidate
    resp = post_to_candidate_resource(access_token)
    resp_dict = resp.json()
    candidate_id = resp_dict['candidates'][0]['id']

    # Fetch Candidate
    resp = get_from_candidate_resource(access_token, candidate_id)
    resp_dict = resp.json()

    # Create Candidate again
    resp = post_to_candidate_resource(access_token, resp_dict)

    return resp


def get_from_candidate_resource(access_token, candidate_id='',
                                candidate_email=''):
    """
    Function sends a get request to CandidateResource via candidate's ID
    or candidate's Email
    i.e. CandidateResource/get()
    """
    url = CandidateResourceUrl.BASE_URL
    if candidate_id:
        url = url + '/%s' % candidate_id
    elif candidate_email:
        url = url + '/%s' % candidate_email

    resp = requests.get(url=url, headers={'Authorization': 'Bearer %s' % access_token})
    return resp


def patch_to_candidate_resource(access_token, data):
    """
    Function sends a patch request to CandidateResource
    """
    resp = requests.patch(
        url=CandidateResourceUrl.BASE_URL,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp


def update_candidate(access_token):
    """
    Function will create a Candidate, retrieve its dict, and update it
    with new values
    """
    # Create a candidate
    create_candidate = post_to_candidate_resource(access_token).json()

    # Fetch Candidate
    candidate_id = create_candidate['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(access_token, candidate_id).json()['candidate']

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
    resp = requests.patch(
        url=CandidateResourceUrl.BASE_URL,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp
