__author__ = 'ufarooqi'
import random
import string
from werkzeug.security import generate_password_hash
from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.models.user import *
import requests
import json

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'

CANDIDATE_POOL_SERVICE_ENDPOINT = 'http://127.0.0.1:8008/%s'
TALENT_POOL_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools'
TALENT_POOL_GROUP_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'groups/%s/talent_pools'
TALENT_POOL_CANDIDATE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools/%s/candidates'


def create_test_user(domain_id, password):
    random_email = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
    email = '%s.sample@example.com' % random_email
    first_name = 'John'
    last_name = 'Sample'
    test_user = User(
        email=email,
        password=generate_password_hash(password, method='pbkdf2:sha512'),
        domain_id=domain_id,
        first_name=first_name,
        last_name=last_name,
        expiration=None
    )
    db.session.add(test_user)
    db.session.commit()
    return test_user


def get_access_token(user, password, client_id, client_secret):
    params = dict(grant_type="password", username=user.email, password=password)
    auth_service_token_response = requests.post(TOKEN_URL,
                                                params=params, auth=(client_id, client_secret)).json()
    if not (auth_service_token_response.get(u'access_token') and auth_service_token_response.get(u'refresh_token')):
        raise Exception("Either Access Token or Refresh Token is missing")
    else:
        return auth_service_token_response.get(u'access_token')


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
