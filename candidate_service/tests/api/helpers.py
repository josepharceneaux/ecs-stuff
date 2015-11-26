"""
Helper functions for tests pertaining to candidate_service's restful services
"""
# Standard library
import requests
import json

# Candidate's sample data
from candidate_sample_data import generate_single_candidate_data


class CandidateResourceUrl:
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


def post_to_candidate_resource(access_token, data=None, domain_id=None):
    """
    Function sends a post request to CandidateResource,
    i.e. CandidateResource/post()
    """
    if not data and domain_id:
        data = generate_single_candidate_data(domain_id=domain_id)
    elif data and not domain_id:
        data = data
    else:
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


def get_from_candidate_resource(access_token, candidate_id='', candidate_email=''):
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


def check_for_id(_dict):
    """
    Checks for id-key in candidate_dict and all its nested objects that must have an id-key
    :return False if an id-key is missing in candidate_dict or any of its nested objects
    """
    # Get top level keys
    top_level_keys = _dict.keys()

    # Top level dict must have an id-key
    if not 'id' in top_level_keys:
        return False

    # Remove id-key from top level keys
    top_level_keys.remove('id')

    # Remove contact_history key since it will not have an id-key to begin with
    if 'contact_history' in top_level_keys:
        top_level_keys.remove('contact_history')

    for key in top_level_keys:
        obj = _dict[key]
        if isinstance(obj, dict):
            # If obj is an empty dict, e.g. obj = {}, continue with the loop
            if not any(obj):
                continue

            check = id_exists(_dict=obj)
            if check is False:
                return check

        if isinstance(obj, list):
            list_of_dicts = obj
            for dictionary in list_of_dicts:
                # Invoke function again if any of dictionary's key's value is a list-of-objects
                for _key in dictionary:
                    if type(dictionary[_key]) == list:
                        for i in range(0, len(dictionary[_key])):
                            check = check_for_id(_dict=dictionary[_key][i])  # recurse
                            if check is False:
                                return check

                check = id_exists(_dict=dictionary)
                if check is False:
                    return check


def id_exists(_dict):
    """
    :return True if id-key is found in _dict, otherwise False
    """
    assert isinstance(_dict, dict)
    check = True
    # Get _dict's keys
    keys = _dict.keys()

    # Ensure id-key exists
    if not 'id' in keys:
        check = False

    return check


def remove_id_key(_dict):
    """
    Function removes the id-key from candidate_dict and all its nested objects
    """
    # Remove contact_history key since it will not have an id-key to begin with
    if 'contact_history' in _dict:
        del _dict['contact_history']

    # Remove id-key from top level dict
    if 'id' in _dict:
        del _dict['id']

    # Get dict-keys
    keys = _dict.keys()

    for key in keys:
        obj = _dict[key]

        if isinstance(obj, dict):
            # If obj is an empty dict, e.g. obj = {}, continue with the loop
            if not any(obj):
                continue
            # Remove id-key if found
            if 'id' in obj:
                del obj['id']

        if isinstance(obj, list):
            list_of_dicts = obj
            for dictionary in list_of_dicts:
                # Remove id-key from each dictionary
                if 'id' in dictionary:
                    del dictionary['id']

                # Invoke function again if any of dictionary's key's value is a list-of-objects
                for _key in dictionary:
                    if isinstance(dictionary[_key], list):
                        for i in range(0, len(dictionary[_key])):
                            remove_id_key(_dict=dictionary[_key][i])  # recurse
    return _dict
    # TODO: remove keys that have None values (can be done in remove_id_key, or maybe a better idea to keep it separate)
    # TODO: check if two objects are identical


# TODO: what if end_date is provided only?
def is_candidate_experience_ordered_correctly(experiences):
    """
    Function will check to see if candidate experience was ordered correctly in return object.
    CandidateExperience must be returned in descending order based on start_date
    :rtype  bool
    """
    assert isinstance(experiences, list)

    latest= experiences[0].get('start_date')
    for i, experience in enumerate(experiences):
        if experience['is_current'] and i != 0:
            return False
        if experience['start_date'] > latest:
            return False

    return True