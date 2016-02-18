import json
import requests
import ConfigParser
from faker import Faker

from ..routes import UserServiceApiUrl

fake = Faker()

OK = 200
CREATED = 201
INVALID_USAGE = 400
NOT_FOUND = 404
FORBIDDEN = 403
INTERNAL_SERVER_ERROR = 500


class TestConfigParser(ConfigParser.ConfigParser):

    def to_dict(self):
        sections = dict(self._sections)
        for k in sections:
            sections[k] = dict(self._defaults, **sections[k])
            sections[k].pop('__name__', None)
        return sections


def send_request(method, url, access_token, data=None, is_json=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


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


def get_non_existing_id(model):
    """
    This functions takes a model class and returns a non existing id
    by getting last object and then adding a large number in it and
    if table is empty, simply return that number
    :param model:
    :return: non_existing_id
    :rtype int | long
    """
    last_obj = model.query.order_by(model.id.desc()).first()
    if last_obj:
        return last_obj.id + 1000
    else:
        return 1000


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
    response = send_request('delete', UserServiceApiUrl.USER_ROLES_API % user_id,
                            token, data=data)
    assert response.status_code == 200

