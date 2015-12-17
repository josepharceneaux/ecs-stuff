__author__ = 'ufarooqi'
import json

import requests

from candidate_pool_service.modules.smartlists import save_smartlist
from candidate_pool_service.common.utils.app_rest_urls import CandidateApiUrl
from candidate_pool_service.common.tests.sample_data import generate_single_candidate_data
CANDIDATE_POOL_SERVICE_ENDPOINT = 'http://127.0.0.1:8008/%s'
TALENT_POOL_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools'
TALENT_POOL_GROUP_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'groups/%s/talent_pools'
TALENT_POOL_CANDIDATE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools/%s/candidates'


def talent_pool_api(access_token, talent_pool_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        if talent_pool_id:
            response = requests.get(url=TALENT_POOL_API + '/%s' % talent_pool_id, headers=headers)
            return response.json(), response.status_code
        else:
            response = requests.get(url=TALENT_POOL_API, headers=headers)
            return response.json(), response.status_code
    elif action == 'DELETE':
        response = requests.delete(url=TALENT_POOL_API + '/%s' % talent_pool_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=TALENT_POOL_API + '/%s' % talent_pool_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_POOL_API, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def talent_pool_group_api(access_token, user_group_id, data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        response = requests.get(url=TALENT_POOL_GROUP_API % user_group_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        headers['content-type'] = 'application/json'
        response = requests.delete(url=TALENT_POOL_GROUP_API % user_group_id, data=json.dumps(data), headers=headers)
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_POOL_GROUP_API % user_group_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    else:
        raise Exception('No valid action is provided')


def talent_pool_candidate_api(access_token, talent_pool_id, data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        response = requests.get(url=TALENT_POOL_CANDIDATE_API % talent_pool_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        headers['content-type'] = 'application/json'
        response = requests.delete(url=TALENT_POOL_CANDIDATE_API % talent_pool_id, data=json.dumps(data), headers=headers)
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_POOL_CANDIDATE_API % talent_pool_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    else:
        raise Exception('No valid action is provided')


# Smartlist functions ===================>
def get_smartlist_candidates(access_token, list_id, candidate_ids_only=False, count_only=False):
    """
    Get all candidates present in smartlist
    :param access_token: authenticated users' access token, will be passed in headers for authorization
    :type access_token: basestring
    :param list_id: smartlist id whose candidates are required
    :type list_id: long | int
    :param candidate_ids_only: if True, will only return candidate ids and count of candidates present in smartlist.
        If False it will return whole candidate's object of candidates present in smartlist
    :type candidate_ids_only: bool
    :param count_only: will only return count of candidates in smartlist
    :type count_only: bool
    :return: response object of GET request
    """
    if candidate_ids_only:
        return_fields = 'candidate_ids_only'
    elif count_only:
        return_fields = 'count_only'
    else:
        return_fields = 'all'
    response = requests.get(
        url= SMARTLIST_CANDIDATES_GET_URL % list_id,
        params={'id': list_id,
                'fields': return_fields},
        headers={'Authorization': 'Bearer %s' % access_token}
    )
    assert response.status_code == 200
    return response


def create_smartlist_with_candidate_ids(user_id, list_name, candidate_ids):
    """ Creates smartlist with candidate_ids
    :param user_id: smartlist owner id
    :param list_name: smartlist name
    :param candidate_ids: List of candidate_ids
    :type candidate_ids: list[int|long]
    :return: Newly created smartlist object
    """
    return save_smartlist(user_id=user_id, name=list_name, candidate_ids=candidate_ids)


def create_smartlist_with_search_params(user_id, list_name, search_params):
    """
    Creates smartlist with search params
    :param user_id: smartlist owner id
    :param list_name: smartlist name
    :param search_params: search parameters
    :type search_params: basestring[dict]
    :return: Newly created smartlist object
    """
    return save_smartlist(user_id=user_id, name=list_name, search_params=search_params)


def create_candidate_from_candidate_api(access_token, data=None):
    """
    Function sends a request to CandidateResource/post()
    """
    if not data:
        data = generate_single_candidate_data()

    resp = requests.post(
        url=CandidateApiUrl.CANDIDATES,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp