__author__ = 'ufarooqi'
import random
import string
from werkzeug.security import generate_password_hash
from user_service.user_app import app
from common.models.user import *
import requests
import json

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'

USER_SERVICE_ENDPOINT = 'http://127.0.0.1:8004/%s'
USER_ROLES = USER_SERVICE_ENDPOINT % 'users/%s/roles'
USER_ROLES_VERIFY = USER_SERVICE_ENDPOINT % 'roles/verify'
USER_DOMAIN_ROLES = USER_SERVICE_ENDPOINT % 'domain/%s/roles'
DOMAIN_GROUPS = USER_SERVICE_ENDPOINT % 'groups'
USER_GROUPS = USER_SERVICE_ENDPOINT % 'groups/%s/users'


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


def user_scoped_roles(access_token, user_id, test_roles=None, action="GET", false_case=False):
    if test_roles:
        test_role_first = test_roles[0]
        test_role_second = test_roles[1]
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(USER_ROLES % user_id, headers=headers)
        if response.status_code == 200:
            response = json.loads(response.text)
            return response.get('roles')
        return response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        test_role_second = DomainRole.get_by_name(test_role_second)
        if false_case:
            data = {'roles': [int(test_role_second.id) + 1]}
        else:
            data = {'roles': [test_role_first, test_role_second.id]}
        response = requests.post(USER_ROLES % user_id, headers=headers, data=json.dumps(data))
        return response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        data = {'roles': [test_role_first, DomainRole.get_by_name(test_role_second).id]}
        response = requests.delete(USER_ROLES % user_id, headers=headers, data=json.dumps(data))
        return response.status_code


def get_roles_of_domain(access_token, domain_id):
    headers = {'Authorization': 'Bearer %s' % access_token}
    response = requests.get(USER_DOMAIN_ROLES % domain_id, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        domain_roles = response.get('roles') or []
        return [domain_role.get('name') for domain_role in domain_roles]
    return response.status_code


def verify_user_scoped_role(user, role):
    user_id = user.get_id()
    response = json.loads(requests.get(USER_ROLES_VERIFY, params={"role": role, "user_id": user_id}).text)
    return response.get('success')


def domain_groups(access_token, domain_id, test_groups=None, action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(DOMAIN_GROUPS, headers=headers, params={'domain_id': domain_id})
        if response.status_code == 200:
            response = json.loads(response.text)
            return [group['name'] for group in response.get('user_groups')]
        return response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        data = {'groups': [{'group_name': group, 'domain_id': domain_id} for group in test_groups]}
        response = requests.post(DOMAIN_GROUPS, headers=headers, data=json.dumps(data))
        db.session.commit()
        return response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        data = {'groups': [group for group in test_groups]}
        response = requests.delete(DOMAIN_GROUPS, headers=headers, data=json.dumps(data))
        return response.status_code


def user_groups(access_token, group_id=None, user_ids=[], action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(USER_GROUPS % group_id, headers=headers)
        if response.status_code == 200:
            response = json.loads(response.text)
            return [user['id'] for user in response.get('users')]
        return response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        data = {'user_ids': user_ids}
        response = requests.post(USER_GROUPS % group_id, headers=headers, data=json.dumps(data))
        return response.status_code
