"""
Helper functions for tests pertaining to candidate_service's restful services
"""
# Standard library
import requests
import json

# Candidate's sample data
from common.tests.sample_data import generate_single_candidate_data


class CandidateResourceUrl():
    def __init__(self):
        pass

    BASE_URL = "http://127.0.0.1:8005/v1/candidates"


def test_response(resp_request, resp_json, resp_status):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    :type resp_json:        dict
    :type resp_status:      int
    """
    inputs = (resp_request, resp_json, resp_status)
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % inputs


def post_to_candidate_resource(access_token):
    """
    Function sends a post request to CandidateResource,
    i.e. CandidateResource/post()
    """
    resp = requests.post(
        url=CandidateResourceUrl.BASE_URL,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(generate_single_candidate_data())
    )
    return resp


def get_from_candidate_resource(access_token, candidate_id=None,
                                candidate_email=None):
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

    resp = requests.get(
        url=url,
        headers={'Authorization': 'Bearer %s' % access_token},
    )
    return resp



