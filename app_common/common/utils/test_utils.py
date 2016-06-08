"""
This module contains utility methods will be used in API based tests.
"""
# Standard imports
import json
import uuid
from datetime import datetime, timedelta

# 3rd party imports
import requests
from faker import Faker
from requests import codes
from contracts import contract
from dateutil.parser import parse

# Service specific imports
from ..error_codes import ErrorCodes
from ..tests.conftest import randomword
from ..routes import (UserServiceApiUrl, AuthApiUrl, CandidateApiUrl,
                      CandidatePoolApiUrl, SchedulerApiUrl)
from ..custom_contracts import define_custom_contracts

define_custom_contracts()
fake = Faker()


@contract
def send_request(method, url, access_token, data=None, params=None, is_json=True, verify=True):
    """
    This is a generic method to send HTTP request. We can just pass our data/ payload
    and it will make it json and send it to target url with application/json as content-type
    header.
    :param http_method method: standard HTTP method like post, get (in lowercase)
    :param string url: target url
    :param (string | None)  access_token: authentication token, token can be empty, None or invalid
    :param (dict | None) data: payload data for request
    :param (dict | None) params: query params
    :param bool is_json: a flag to determine, whether we need to dump given data or not.
            default value is true because most of the APIs are using json content-type.
    :param bool verify: set this to false
    :return:
    """
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, params=params, headers=headers, verify=verify)


def response_info(response):
    """
    Function returns the following response information if available:
        1. Url, 2. Request 3. Response dict, and 4. Response status code
    :type response: requests.models.Response
    """
    status_code = response.status_code if hasattr(response, 'status_code') else None
    url = response.url if hasattr(response, 'url') else None
    request = response.request if hasattr(response, 'request') else None
    try:
        jsoned = response.json()
    except Exception:
        jsoned = None

    content = "\nUrl: {}\nRequest: {}\nStatus code: {}\nResponse JSON: {}"
    return content.format(url, request, status_code, jsoned)


@contract
def get_user(user_id, token):
    """
    This utility is used to get user info from UserService
    :param user_id: user unique identifier
    :type user_id: int | long
    :param token: authentication token for user
    :type token: string
    :return: user dictionary
    :rtype: dict
    """
    response = send_request('get', UserServiceApiUrl.USER % user_id, token)
    print('common_tests : get_user: ', response.content)
    assert response.status_code == codes.OK
    return response.json()['user']


@contract
def refresh_token(data):
    """
    This utility function gets required data (client_id, client_secret, refresh_token)
    from data (dict) and refreshes token from AuthService
    :param dict data: a dictionary containing client info
    :return: auth token for user
    :rtype: string
    """
    data = {'client_id': data.get('client_id'),
            'client_secret': data.get('client_secret'),
            'refresh_token': data.get('refresh_token'),
            'grant_type': 'refresh_token'
            }
    resp = requests.post(AuthApiUrl.TOKEN_CREATE, data=data)
    print('common_tests : refresh_token: ', resp.content)
    assert resp.status_code == codes.OK
    resp = resp.json()
    return resp['access_token']


@contract
def get_token(info):
    """
    This utility function gets required data (client_id, client_secret, username, password)
    from info (dict) and retrieves token from AuthService
    :param info: a dictionary containing client info
    :type info: dict
    :return: auth token for user
    :rtype: string
    """
    data = {'client_id': info.get('client_id'),
            'client_secret': info.get('client_secret'),
            'username': info.get('username'),
            'password': info.get('password'),
            'grant_type': 'password'
            }
    resp = requests.post(AuthApiUrl.TOKEN_CREATE, data=data)
    print('common_tests : get_token: ', resp.content)
    assert resp.status_code == codes.OK
    resp = resp.json()
    access_token = resp['access_token']
    data.update(resp)
    one_minute_later = datetime.utcnow() + timedelta(seconds=60)
    if parse(resp['expires_at']) < one_minute_later:
        access_token = refresh_token(data)
    return access_token


@contract
def unauthorize_test(method, url, data=None):
    """
    This method is used to test for unauthorized requests (401).
    :param http_method method: http method
    :param string url: target url
    :param (dict | None) data: dictionary payload
    :return:
    """
    response = send_request(method, url, 'invalid_token',  data)
    print('common_tests : unauthorize_test: ', response.content)
    assert response.status_code == codes.UNAUTHORIZED


@contract
def invalid_data_test(method, url, token):
    """
    This functions sends http request to a given url with different
    invalid data and checks for InvalidUsage
    :param http_method method: http method e.g. POST, PUT
    :param string url: api url
    :param string token: auth token
    :return:
    """
    data = None
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == codes.BAD_REQUEST
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == codes.BAD_REQUEST
    data = {}
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == codes.BAD_REQUEST
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == codes.BAD_REQUEST
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == codes.BAD_REQUEST


@contract
def get_fake_dict(key_count=3):
    """
    This method just creates a dictionary with 3 random keys and values
    :param key_count: number of keys and values in dictionary
    :type key_count: int
    : Example:

        data = {
                    'excepturi': 'qui',
                    'unde': 'ipsam',
                    'magni': 'voluptate'
                }
    :return: data
    :rtype dict
    """
    data = dict()
    for _ in range(key_count):
        data[fake.word()] = fake.word()
    return data


@contract
def add_roles(user_id, roles, token):
    """
    This method sends a POST request to UserService to add given roles to given user
    :param ((int | long), >0) user_id: user unique id in gt database
    :param list | tuple roles: permissions list
    :param string token: auth token
    """
    assert roles, 'roles should be a non-empty list or tuple, given: %s' % roles
    assert token, 'token should be a non-empty string, given: %s' % token
    for role in roles:
        data = {"roles": [role]}
        response = send_request('post', UserServiceApiUrl.USER_ROLES_API % user_id,
                                token, data=data)
        if response.status_code == codes.BAD_REQUEST:
            assert response.json()['error']['code'] == ErrorCodes.ROLE_ALREADY_EXISTS
        else:
            assert response.status_code == codes.OK


@contract
def remove_roles(user_id, roles, token):
    """
    This method sends a DELETE request to UserService to remove given roles to given user
    :param (int | long) user_id: id of user
    :param list[>0] roles: permissions list
    :param string token: auth token
    """
    data = {
        "roles": roles
    }
    response = send_request('delete', UserServiceApiUrl.USER_ROLES_API % user_id,
                            token, data=data)
    print('common_tests : remove_roles: ', response.content)
    assert response.status_code in [codes.OK, codes.BAD_REQUEST]


@contract
def delete_scheduler_task(task_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to Scheduler API to delete  a scheduled task.
    :type task_id: string
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', SchedulerApiUrl.TASK % task_id, token)
    print('common_tests : delete_scheduler: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def create_candidate(talent_pool_id, token, expected_status=(201,)):
    """
    This method sends a POST request to Candidate API to create  a candidate.
    :type talent_pool_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    data = {
        "candidates": [
            {
                "first_name": fake.first_name(),
                "middle_name": fake.user_name(),
                "last_name": fake.last_name(),
                "talent_pool_ids": {
                    "add": [talent_pool_id]
                },
                "emails": [
                    {
                        "label": "Primary",
                        "address": fake.safe_email(),
                        "is_default": True
                    }
                ]
            }

        ]
    }
    response = send_request('post', CandidateApiUrl.CANDIDATES, token, data=data)
    print('common_tests : create_candidate: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def get_candidate(candidate_id, token, expected_status=(200,)):
    """
    This method sends a GET request to Candidate API to get a candidate info.
    :type candidate_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token)
    print('common_tests : get_candidate: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def search_candidates(candidate_ids, token, expected_status=(200,)):
    """
    This method sends a GET request to Candidate Search API to get candidates from CloudSearch.
    :type candidate_ids: list|tuple
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    params = {'candidate_ids': candidate_ids}
    response = send_request('get', CandidateApiUrl.CANDIDATE_SEARCH_URI, token, data=params)
    print('common_tests : get_candidate: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def delete_candidate(candidate_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to Candidate API to delete a candidate given by candidate_id.
    :type candidate_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_id, token)
    print('common_tests : delete_candidate: ', response.content)
    assert response.status_code in expected_status


@contract
def create_smartlist(candidate_ids, talent_pipeline_id, token, expected_status=(201,)):
    """
    This method sends a POST request to CandidatePool API to create a smartlist.
    :type candidate_ids: list|tuple
    :type talent_pipeline_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    data = {
        'candidate_ids': candidate_ids,
        'name': fake.word(),
        "talent_pipeline_id": talent_pipeline_id
    }
    response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, token, data=data)
    print('common_tests : create_smartlist: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def delete_smartlist(smartlist_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to CandidatePool API to delete a smartlist.
    :type smartlist_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidatePoolApiUrl.SMARTLIST % smartlist_id, token)
    print('common_tests : delete_smartlist: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def get_smartlist_candidates(smartlist_id, token, expected_status=(200,), count=None):
    """
    This method sends a GET request to CandidatePool API to get list of candidates associated to  a smartlist.
    :type smartlist_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """

    response = send_request('get', CandidatePoolApiUrl.SMARTLIST_CANDIDATES % smartlist_id, token)
    print('common_tests : get_smartlist_candidates: ', response.content)
    assert response.status_code in expected_status
    response = response.json()
    if count:
        assert len(response['candidates']) == count
    return response


@contract
def create_talent_pipelines(token, talent_pool_id, count=1, expected_status=(200,)):
    """
    This method sends a POST request to CandidatePool API to create  a talent pipeline.
    :type token: string
    :type talent_pool_id: int | long
    :type count: int
    :type expected_status: tuple[int]
    :rtype dict
    """
    data = {
        "talent_pipelines": []
    }
    for index in xrange(count):
        talent_pipeline = {
              "name": randomword(30),
              "description": fake.paragraph(),
              "talent_pool_id": talent_pool_id,
              "date_needed": (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d")
        }
        data["talent_pipelines"].append(talent_pipeline)
    response = send_request('post', CandidatePoolApiUrl.TALENT_PIPELINES, token, data=data)
    print('common_tests : create_talent_pipelines: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def get_talent_pipeline(talent_pipeline_id, token, expected_status=(200,)):
    """
    This method sends a GET request to CandidatePool API to get talent pipeline.
    :type talent_pipeline_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', CandidatePoolApiUrl.TALENT_PIPELINE % talent_pipeline_id, token)
    print('common_tests : get_talent_pipeline: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def delete_talent_pipeline(talent_pipeline_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to CandidatePool API to delete a specific talent pipeline.
    :type talent_pipeline_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidatePoolApiUrl.TALENT_PIPELINE % talent_pipeline_id,
                            token)
    print('common_tests : delete_talent_pipeline: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def create_talent_pools(token, count=1, expected_status=(200,)):
    """
    This method sends a POST request to CandidatePool API to create a talent pool.
    :type token: string
    :type count: int | long
    :type expected_status: tuple[int]
    :rtype dict
    """
    data = {
        "talent_pools": []
    }
    for index in xrange(count):
        talent_pool = {
                "name": str(uuid.uuid4())[:20],
                "description": fake.paragraph()
            }
        data["talent_pools"].append(talent_pool)
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOLS, token, data=data)
    print('common_tests : create_talent_pools: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def get_talent_pool(talent_pool_id, token, expected_status=(200,)):
    """
    This method sends a GET request to CandidatePool API to get a specific talent pool.
    :type talent_pool_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id, token)
    print('common_tests : get_talent_pool: ', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def delete_talent_pool(talent_pool_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to CandidatePool API to delete a talent pool.
    :type talent_pool_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token)
    print('common_tests : delete_talent_pool: ', response.content)
    assert response.status_code in expected_status
    return response.json()
