"""
This module contains utility methods will be used in API based tests.
"""
import json

from datetime import datetime, timedelta
from dateutil.parser import parse
import requests
from requests import codes
from faker import Faker

from ..tests.conftest import randomword
from ..error_codes import ErrorCodes
from ..routes import UserServiceApiUrl, AuthApiUrl, CandidateApiUrl, CandidatePoolApiUrl, \
    SchedulerApiUrl

fake = Faker()


def send_request(method, url, access_token, data=None, is_json=True, verify=True):
    """
    This is a generic method to send HTTP request. We can just pass our data/ payload
    and it will make it json and send it to target url with application/json as content-type
    header.
    :param method: standard HTTP method like post, get (in lowercase)
    :param url: target url
    :param access_token: authentication token, token can be empty, None or invalid
    :param data: payload data for request
    :param is_json: a flag to determine, whether we need to dump given data or not.
            default value is true because most of the APIs are using json content-type.
    :param verify: set this to false 
    :return:
    """
    assert method in ['get', 'post', 'put', 'delete', 'patch'], 'Invalid method'
    assert url and isinstance(url, basestring), 'url must have a valid string value'
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers, verify=verify)


def response_info(response):
    """
    Function returns the following response information:
        1. Url, 2. Request 3. Response dict if any, and 4. Response status code
    :type response: requests.models.Response
    """
    url, request, status_code = response.url, response.request, response.status_code
    try:
        _json = response.json()
    except Exception:
        _json = None

    content = "\nUrl: {}\nRequest: {}\nStatus code: {}\nResponse JSON: {}"
    return content.format(url, request, status_code, _json)


def get_user(user_id, token):
    """
    This utility is used to get user info from UserService
    :param user_id: user unique identifier
    :type user_id: int | long
    :param token: authentication token for user
    :type token: str
    :return: user dictionary
    :rtype: dict
    """
    assert isinstance(token, basestring), \
        'token must be a string, given type is %s' % type(token)
    assert str(user_id).isdigit(), 'user_id must be valid number'
    response = send_request('get', UserServiceApiUrl.USER % user_id, token)
    print('common_tests : get_user: ', response.content)
    assert response.status_code == codes.OK
    return response.json()['user']


def refresh_token(data):
    """
    This utility function gets required data (client_id, client_secret, refresh_token)
    from data (dict) and refreshes token from AuthService
    :param data: a dictionary containing client info
    :type data: dict
    :return: auth token for user
    :rtype: str
    """
    assert isinstance(data, dict), 'info must be dictionary'
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


def get_token(info):
    """
    This utility function gets required data (client_id, client_secret, username, password)
    from info (dict) and retrieves token from AuthService
    :param info: a dictionary containing client info
    :type info: dict
    :return: auth token for user
    :rtype: str
    """
    assert isinstance(info, dict), 'info must be dictionary'
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
    if parse(resp['expires_at']) < (datetime.now() + timedelta(seconds=60)):
        access_token = refresh_token(data)
    return access_token


def unauthorize_test(method, url, data=None):
    """
    This method is used to test for unauthorized requests (401).
    :param method: http method
    :param url: target url
    :param data: dictionary payload
    :return:
    """
    response = send_request(method, url, 'invalid_token',  data)
    print('common_tests : unauthorize_test: ', response.content)
    assert response.status_code == codes.UNAUTHORIZED


def invalid_data_test(method, url, token):
    """
    This functions sends http request to a given url with different
    invalid data and checks for InvalidUsage
    :param method: http method e.g. POST, PUT
    :param url: api url
    :param token: auth token
    :return:
    """
    assert method in ['get', 'post', 'put', 'delete', 'patch'], 'Invalid method'
    assert url and isinstance(url, basestring), 'url must have a valid string value'
    assert token and isinstance(token, basestring), 'token must have a valid string value'
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


def add_roles(user_id, roles, token):
    """
    This method sends a POST request to UserService to add given roles to given user
    :param user_id: id of user
    :param roles: permissions list
    :param token: auth token
    :return: True | False
    """

    for role in roles:
        data = {"roles": [role]}
        response = send_request('post', UserServiceApiUrl.USER_ROLES_API % user_id,
                                token, data=data)
        if response.status_code == codes.BAD_REQUEST:
            assert response.json()['error']['code'] == ErrorCodes.ROLE_ALREADY_EXISTS
        else:
            assert response.status_code == codes.OK


def remove_roles(user_id, roles, token):
    """
    This method sends a DELETE request to UserService to remove given roles to given user
    :param user_id: id of user
    :param roles: permissions list
    :param token: auth token
    :return: True | False
    """
    data = {
        "roles": roles
    }
    response = send_request('delete', UserServiceApiUrl.USER_ROLES_API % user_id,
                            token, data=data)
    print('common_tests : remove_roles: ', response.content)
    assert response.status_code in [codes.OK, codes.BAD_REQUEST]


def delete_scheduler_task(task_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to Scheduler API to delete  a scheduled task.
    :type task_id: str
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', SchedulerApiUrl.TASK % task_id, token)
    print('common_tests : delete_scheduler: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def create_candidate(talent_pool_id, token, expected_status=(201,)):
    """
    This method sends a POST request to Candidate API to create  a candidate.
    :type talent_pool_id: int | long
    :type token: str
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


def get_candidate(candidate_id, token, expected_status=(200,)):
    """
    This method sends a GET request to Candidate API to get a candidate info.
    :type candidate_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token)
    print('common_tests : get_candidate: ', response.content)
    assert response.status_code in expected_status
    return response.json()


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


def create_smartlist(candidate_ids, talent_pipeline_id, token, expected_status=(201,)):
    """
    This method sends a POST request to CandidatePool API to create a smartlist.
    :type candidate_ids: list[int]
    :type talent_pipeline_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    assert isinstance(candidate_ids, (list, tuple)), 'candidate_ids must be list or tuple'
    data = {
        'candidate_ids': candidate_ids,
        'name': fake.word(),
        "talent_pipeline_id": talent_pipeline_id
    }
    response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, token, data=data)
    print('common_tests : create_smartlist: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_smartlist(smartlist_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to CandidatePool API to delete a smartlist.
    :type smartlist_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidatePoolApiUrl.SMARTLIST % smartlist_id, token)
    print('common_tests : delete_smartlist: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def get_smartlist_candidates(smartlist_id, token, expected_status=(200,), count=None):
    """
    This method sends a GET request to CandidatePool API to get list of candidates associated to  a smartlist.
    :type smartlist_id: int | long
    :type token: str
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


def create_talent_pipelines(token, talent_pool_id, count=1, expected_status=(200,)):
    """
    This method sends a POST request to CandidatePool API to create  a talent pipeline.
    :type token: str
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


def get_talent_pipeline(talent_pipeline_id, token, expected_status=(200,)):
    """
    This method sends a GET request to CandidatePool API to get talent pipeline.
    :type talent_pipeline_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', CandidatePoolApiUrl.TALENT_PIPELINE % talent_pipeline_id, token)
    print('common_tests : get_talent_pipeline: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_talent_pipeline(talent_pipeline_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to CandidatePool API to delete a specific talent pipeline.
    :type talent_pipeline_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidatePoolApiUrl.TALENT_PIPELINE % talent_pipeline_id,
                            token)
    print('common_tests : delete_talent_pipeline: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def create_talent_pools(token, count=1, expected_status=(200,)):
    """
    This method sends a POST request to CandidatePool API to create a talent pool.
    :type token: str
    :type count: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    data = {
        "talent_pools": []
    }
    for index in xrange(count):
        talent_pool = {
                "name": randomword(20),
                "description": fake.paragraph()
            }
        data["talent_pools"].append(talent_pool)
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOLS, token, data=data)
    print('common_tests : create_talent_pools: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def get_talent_pool(talent_pool_id, token, expected_status=(200,)):
    """
    This method sends a GET request to CandidatePool API to get a specific talent pool.
    :type talent_pool_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id, token)
    print('common_tests : get_talent_pool: ', response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_talent_pool(talent_pool_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to CandidatePool API to delete a talent pool.
    :type talent_pool_id: int | long
    :type token: str
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token)
    print('common_tests : delete_talent_pool: ', response.content)
    assert response.status_code in expected_status
    return response.json()
