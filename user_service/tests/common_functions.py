__author__ = 'ufarooqi'
import requests
import json
from user_service.user_app import db
from user_service.common.models.user import DomainRole

USER_SERVICE_ENDPOINT = 'http://127.0.0.1:8004/%s'
USER_ROLES = USER_SERVICE_ENDPOINT % 'users/%s/roles'
USER_ROLES_VERIFY = USER_SERVICE_ENDPOINT % 'roles/verify'
USER_DOMAIN_ROLES = USER_SERVICE_ENDPOINT % 'domain/%s/roles'
DOMAIN_GROUPS = USER_SERVICE_ENDPOINT % 'domain/%s/groups'
DOMAIN_GROUPS_UPDATE = USER_SERVICE_ENDPOINT % 'domain/groups/%s'
USER_GROUPS = USER_SERVICE_ENDPOINT % 'groups/%s/users'
UPDATE_PASSWORD = USER_SERVICE_ENDPOINT % 'users/update_password'

USER_API = USER_SERVICE_ENDPOINT % 'users'
DOMAIN_API = USER_SERVICE_ENDPOINT % 'domains'


def user_scoped_roles(access_token, user_id, test_roles=None, action="GET", false_case=False):
    if test_roles:
        test_role_first = test_roles[0]
        test_role_second = test_roles[1]
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(USER_ROLES % user_id, headers=headers)
        return response.json(), response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        test_role_second = DomainRole.get_by_name(test_role_second)
        if false_case:
            data = {'roles': [int(test_role_second.id) + 10]}
        else:
            data = {'roles': [test_role_first, test_role_second.id]}
        response = requests.post(USER_ROLES % user_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        data = {'roles': [test_role_first, DomainRole.get_by_name(test_role_second).id]}
        response = requests.delete(USER_ROLES % user_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def get_roles_of_domain(access_token, domain_id):
    headers = {'Authorization': 'Bearer %s' % access_token}
    response = requests.get(USER_DOMAIN_ROLES % domain_id, headers=headers)
    return response.json(), response.status_code


def domain_groups(access_token, domain_id=None, data=None, group_id=None, action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(DOMAIN_GROUPS % domain_id, headers=headers, params={'domain_id': domain_id})
        return response.json(), response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        response = requests.post(DOMAIN_GROUPS % domain_id, headers=headers, data=json.dumps(data))
        db.session.commit()
        return response.json(), response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        response = requests.delete(DOMAIN_GROUPS % domain_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == "PUT":
        headers['content-type'] = 'application/json'
        response = requests.put(DOMAIN_GROUPS_UPDATE % group_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def user_groups(access_token, group_id, user_ids=[], action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(USER_GROUPS % group_id, headers=headers)
        return response.json(), response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        data = {'user_ids': user_ids}
        response = requests.post(USER_GROUPS % group_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def update_password(access_token, old_password, new_password):
    headers = {'Authorization': 'Bearer %s' % access_token, 'content-type': 'application/json'}
    data = {"old_password": old_password, "new_password": new_password}
    response = requests.put(url=UPDATE_PASSWORD, headers=headers, data=json.dumps(data))
    return response.status_code


def user_api(access_token, user_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        if user_id:
            response = requests.get(url=USER_API + '/%s' % user_id, headers=headers)
            return response.json(), response.status_code
        else:
            response = requests.get(url=USER_API, headers=headers)
            return response.json(), response.status_code
    elif action == 'DELETE':
        response = requests.delete(url=USER_API + '/%s' % user_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=USER_API + '/%s' % user_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=USER_API, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def domain_api(access_token, domain_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        url = DOMAIN_API + '/%s' % domain_id if domain_id else DOMAIN_API
        response = requests.get(url=url, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        url = DOMAIN_API + '/%s' % domain_id if domain_id else DOMAIN_API
        response = requests.delete(url=url, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=DOMAIN_API + '/%s' % domain_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=DOMAIN_API, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
