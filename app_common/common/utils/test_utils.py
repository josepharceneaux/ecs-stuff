import json
import requests
from faker import Faker

from ..routes import UserServiceApiUrl, AuthApiUrl

fake = Faker()

OK = 200
CREATED = 201
INVALID_USAGE = 400
NOT_FOUND = 404
FORBIDDEN = 403
INTERNAL_SERVER_ERROR = 500


def send_request(method, url, access_token, data=None, is_json=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


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
    assert response.status_code == 200
    return response.json()['user']


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
    assert resp.status_code == 200
    token = resp.json()['access_token']
    return token


def unauthorize_test(method, url, access_token, data=None):
    # TODO: Use a hard coded token invalid
    response = send_request(method, url, access_token,  data)
    assert response.status_code == 401


def invalid_data_test(method, url, token):
    """
    This functions sends http request to a given url with different
    invalid data and checks for InvalidUsage
    :param method: http method e.g. POST, PUT
    :param url: api url
    :param token: auth token
    :return:
    """
    data = None
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == INVALID_USAGE
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == INVALID_USAGE
    data = {}
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == INVALID_USAGE
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == INVALID_USAGE
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == INVALID_USAGE


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
    data = {
        "roles": roles
    }
    response = send_request('post', UserServiceApiUrl.USER_ROLES_API % user_id,
                            token, data=data)
    if response.status_code == 400 and response.json()['error']['code'] == 9000:
        return None
    assert response.status_code == 200


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
    send_request('delete', UserServiceApiUrl.USER_ROLES_API % user_id,
                 token, data=data)
