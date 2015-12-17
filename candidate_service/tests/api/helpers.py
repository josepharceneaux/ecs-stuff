"""
Helper functions for tests pertaining to candidate_service's restful services
"""
# Standard library
import requests
import json

# Candidate's sample data
from candidate_sample_data import generate_single_candidate_data

# Candidate REST urls
from candidate_service.common.routes import CandidateApiUrl


def define_and_send_request(request, url, access_token):
    """
    Function will define request based on params and make the appropriate call.
    :param  request:  can only be get, post, put, patch, or delete
    """
    request = request.lower()
    assert request in ['get', 'post', 'put', 'patch', 'delete']
    method = getattr(requests, request)
    return method(url=url, headers={'Authorization': 'Bearer %s' % access_token})


def response_info(response):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    """
    request = response.request
    _json = None if response.reason == 'NOT FOUND' or not any(response.text) else response.json()
    status_code = response.status_code
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % (request, _json, status_code)


def post_to_candidate_resource(access_token, data=None, domain_id=None):
    """
    Function sends a request to CandidateResource/post()
    If domain_id is provided, data will include candidate aoi & custom fields
    """
    if not data and domain_id:
        data = generate_single_candidate_data(domain_id=domain_id)
    elif data and not domain_id:
        data = data
    else:
        data = generate_single_candidate_data()

    resp = requests.post(
        url=CandidateApiUrl.CANDIDATES,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp


def get_from_candidate_resource(access_token, candidate_id='', candidate_email=''):
    """
    Function sends a get request to CandidateResource/get()
    """
    url = CandidateApiUrl.CANDIDATES
    if candidate_id:
        url = url + '/%s' % candidate_id
    elif candidate_email:
        url = url + '/%s' % candidate_email

    resp = requests.get(url=url, headers={'Authorization': 'Bearer %s' % access_token})
    return resp


def patch_to_candidate_resource(access_token, data):
    """
    Function sends a request to CandidateResource/patch()
    """
    resp = requests.patch(
        url=CandidateApiUrl.CANDIDATES,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp


def request_to_candidate_resource(access_token, request, candidate_id='', candidate_email=''):
    """
    Function sends a request to CandidateResource
    :param request: get, post, patch, delete
    """
    url = CandidateApiUrl.CANDIDATES
    if candidate_id:
        url = CandidateApiUrl.CANDIDATE % candidate_id
    elif candidate_email:
        url = CandidateApiUrl.CANDIDATE % candidate_email

    return define_and_send_request(request, url, access_token)


def request_to_candidate_address_resource(access_token, request, candidate_id='',
                                          all_addresses=False, address_id=''):
    """
    Function sends a request to CandidateAddressResource.
    If all_addresses is True, the request will hit /.../addresses endpoint.
    :param  request: delete
    """
    if all_addresses:
        url = CandidateApiUrl.ADDRESSES % candidate_id
    else:
        url = CandidateApiUrl.ADDRESS % (candidate_id, address_id)

    return define_and_send_request(request=request, url=url, access_token=access_token)


def request_to_candidate_aoi_resource(access_token, request, candidate_id='', all_aois=False, aoi_id=None):
    """
    Function sends a request to CandidateAreaOfInterestResource.
    If can_aois is True, the request will hit /areas_of_interest endpoint.
    :param request: delete
    """
    if all_aois:
        url = CandidateApiUrl.AOIS % candidate_id
    else:
        url = CandidateApiUrl.AOI % (candidate_id, aoi_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_custom_field_resource(access_token, request, candidate_id='',
                                               all_custom_fields=False, custom_field_id=''):
    """
    Function sends a request to CandidateCustomFieldResource.
    If all_custom_fields is True, the request will hit /.../custom_fields endpoint
    :param request: delete
    """
    if all_custom_fields:
        url = CandidateApiUrl.CUSTOM_FIELDS % candidate_id
    else:
        url = CandidateApiUrl.CUSTOM_FIELD % (candidate_id, custom_field_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_education_resource(access_token, request, candidate_id='',
                                            all_educations=False, education_id=None):
    """
    Function sends a request to CandidateEducationResource.
    If all_educations is True, the request will hit /educations endpoint.
    :param request: delete
    """
    if all_educations:
        url = CandidateApiUrl.EDUCATIONS % candidate_id
    else:
        url = CandidateApiUrl.EDUCATION % (candidate_id, education_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_education_degree_resource(access_token, request, candidate_id='',
                                                   education_id=None, all_degrees=False,
                                                   degree_id=None):
    """
    Function sends a request to CandidateEducationDegreeResource.
    If all_degrees is True, the request will hit /.../degrees endpoint.
    :param request: delete
    """
    if all_degrees:
        url = CandidateApiUrl.DEGREES % (candidate_id, education_id)
    else:
        url = CandidateApiUrl.DEGREE % (candidate_id, education_id, degree_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_education_degree_bullet_resource(access_token, request,
                                                          candidate_id='',
                                                          education_id='',
                                                          degree_id='',
                                                          all_bullets=False,
                                                          bullet_id=''):
    """
    Function sends a request to CandidateEducationDegreeBulletResource.
    If all_bullets is True, the request will hit /.../bullets endpoint.
    :param request: delete
    """
    if all_bullets:
        url = CandidateApiUrl.DEGREE_BULLETS % (candidate_id, education_id, degree_id)
    else:
        url = CandidateApiUrl.DEGREE_BULLET % (candidate_id, education_id, degree_id, bullet_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_experience_resource(access_token, request, candidate_id='',
                                             all_experiences=False, experience_id=''):
    """
    Function sends a request to CandidateExperienceResource.
    If all_experiences is True, the request will hit /.../experiences endpoint.
    :param request: delete
    """
    if all_experiences:
        url = CandidateApiUrl.EXPERIENCES % candidate_id
    else:
        url = CandidateApiUrl.EXPERIENCE % (candidate_id, experience_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_experience_bullet_resource(access_token, request, candidate_id='',
                                                    experience_id='', all_bullets=False, bullet_id=''):
    """
    Function sends a request to CandidateExperienceBulletResource.
    If all_bullets is True, the request will hit /.../bullets endpoint.
    :param request: delete
    """
    if all_bullets:
        url = CandidateApiUrl.EXPERIENCE_BULLETS % (candidate_id, experience_id)
    else:
        url = CandidateApiUrl.EXPERIENCE_BULLET % (candidate_id, experience_id, bullet_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_email_resource(access_token, request, candidate_id='', all_emails=False, email_id=''):
    """
    Function sends a request to CandidateEmailResource
    If all_emails is True, the request will hit /.../emails endpoint.
    :param request: delete
    """
    if all_emails:
        url = CandidateApiUrl.EMAILS % candidate_id
    else:
        url = CandidateApiUrl.EMAIL % (candidate_id, email_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_military_service(access_token, request, candidate_id='',
                                          all_military_services=False, military_service_id=''):
    """
    Function sends a request to CandidateMilitaryServiceResource
    If all_military_services is True, the request will hit /.../military_services endpoint.
    :param request: delete
    """
    if all_military_services:
        url = CandidateApiUrl.MILITARY_SERVICES % candidate_id
    else:
        url = CandidateApiUrl.MILITARY_SERVICE % (candidate_id, military_service_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_phone_resource(access_token, request, candidate_id='', all_phones=False, phone_id=''):
    """
    Function sends a request to CandidatePhoneResource
    If all_phones is True, the request will hit /.../phones endpoint.
    :param request: delete
    """
    if all_phones:
        url = CandidateApiUrl.PHONES % candidate_id
    else:
        url = CandidateApiUrl.PHONE % (candidate_id, phone_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_preferred_location_resource(access_token, request, candidate_id='',
                                                     all_preferred_locations=False, preferred_location_id=''):
    """
    Function sends a request to CandidatePreferredLocationResource
    If all_preferred_location is True, the request will hit /.../preferred_locations endpoint
    :param request: delete
    """
    if all_preferred_locations:
        url = CandidateApiUrl.PREFERRED_LOCATIONS % candidate_id
    else:
        url = CandidateApiUrl.PREFERRED_LOCATION % (candidate_id, preferred_location_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_skill_resource(access_token, request, candidate_id='', all_skills=False, skill_id=''):
    """
    Function sends a request to CandidateSkillResource
    If all_skills is True, the request will hit /.../skills endpoint.
    :param request: delete
    """
    if all_skills:
        url = CandidateApiUrl.SKILLS % candidate_id
    else:
        url = CandidateApiUrl.SKILL % (candidate_id, skill_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_social_network_resource(access_token, request, candidate_id='', all_sn=False, sn_id=''):
    """
    Function sends a request to CandidateSocialNetwork
    If all_social_network is True, the request will hit /.../social_networks endpoint
    :param request: delete
    """
    if all_sn:
        url = CandidateApiUrl.SOCIAL_NETWORKS % candidate_id
    else:
        url = CandidateApiUrl.SOCIAL_NETWORK % (candidate_id, sn_id)

    return define_and_send_request(request, url, access_token)


def request_to_candidate_work_preference_resource(access_token, request, candidate_id='', work_preference_id=''):
    """
    Function sends a request to CandidateWorkPreferenceResource
    :param request: delete
    """
    url = CandidateApiUrl.WORK_PREFERENCE % (candidate_id, work_preference_id)
    return define_and_send_request(request, url, access_token)


def request_to_candidate_edit_resource(access_token, request, candidate_id=''):
    """
    :param access_token:
    :param request: get
    """
    url = CandidateApiUrl.CANDIDATE_EDIT % candidate_id
    return define_and_send_request(request, url, access_token)


def create_same_candidate(access_token):
    """
    Function will attempt to create the same Candidate twice
    """
    # Create Candidate
    resp = post_to_candidate_resource(access_token)
    resp_dict = resp.json()
    candidate_id = resp_dict['candidates'][0]['id']

    # Fetch Candidate\
    resp = get_from_candidate_resource(access_token, candidate_id)
    resp_dict = resp.json()

    # Create Candidate again
    resp = post_to_candidate_resource(access_token, resp_dict)

    return resp


def check_for_id(_dict):
    """
    Checks for id-key in candidate_dict and all its nested objects that must have an id-key
    :type _dict:    dict
    :return False if an id-key is missing in candidate_dict or any of its nested objects
    """
    assert isinstance(_dict, dict)
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


# # TODO: what if end_date is provided only?
# def is_candidate_experience_ordered_correctly(experiences):
#     """
#     Function will check to see if candidate experience was ordered correctly in return object.
#     CandidateExperience must be returned in descending order based on start_date
#     :rtype  bool
#     """
#     assert isinstance(experiences, list)
#
#     latest= experiences[0].get('start_date')
#     for i, experience in enumerate(experiences):
#         if experience['is_current'] and i != 0:
#             return False
#         if experience['start_date'] > latest:
#             return False
#
#     return True
