__author__ = 'ufarooqi'
import requests
import json
from user_service.user_app import db
from user_service.common.models.user import DomainRole
from user_service.common.routes import UserServiceApiUrl


def user_scoped_roles(access_token, user_id, test_roles=None, action="GET", false_case=False):
    if test_roles:
        test_role_first = test_roles[0]
        test_role_second = test_roles[1]
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(UserServiceApiUrl.USER_ROLES_API % user_id, headers=headers)
        return response.json(), response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        test_role_second = DomainRole.get_by_name(test_role_second)
        if false_case:
            data = {'roles': [int(test_role_second.id) + 10]}
        else:
            data = {'roles': [test_role_first, test_role_second.id]}
        response = requests.post(UserServiceApiUrl.USER_ROLES_API % user_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        data = {'roles': [test_role_first, DomainRole.get_by_name(test_role_second).id]}
        response = requests.delete(UserServiceApiUrl.USER_ROLES_API % user_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def get_roles_of_domain(access_token, domain_id):
    headers = {'Authorization': 'Bearer %s' % access_token}
    response = requests.get(UserServiceApiUrl.DOMAIN_ROLES_API % domain_id, headers=headers)
    return response.json(), response.status_code


def domain_groups(access_token, domain_id=None, data=None, group_id=None, action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(UserServiceApiUrl.DOMAIN_GROUPS_API % domain_id, headers=headers,
                                params={'domain_id': domain_id})
        return response.json(), response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        response = requests.post(UserServiceApiUrl.DOMAIN_GROUPS_API % domain_id, headers=headers, data=json.dumps(data))
        db.session.commit()
        return response.json(), response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        response = requests.delete(UserServiceApiUrl.DOMAIN_GROUPS_API % domain_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == "PUT":
        headers['content-type'] = 'application/json'
        response = requests.put(UserServiceApiUrl.DOMAIN_GROUPS_UPDATE_API % group_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def user_groups(access_token, group_id, user_ids=[], action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == "GET":
        response = requests.get(UserServiceApiUrl.USER_GROUPS_API % group_id, headers=headers)
        return response.json(), response.status_code
    elif action == "POST":
        headers['content-type'] = 'application/json'
        data = {'user_ids': user_ids}
        response = requests.post(UserServiceApiUrl.USER_GROUPS_API % group_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def update_password(access_token, old_password, new_password):
    headers = {'Authorization': 'Bearer %s' % access_token, 'content-type': 'application/json'}
    data = {"old_password": old_password, "new_password": new_password}
    response = requests.put(url=UserServiceApiUrl.UPDATE_PASSWORD_API, headers=headers, data=json.dumps(data))
    return response.status_code


def forgot_password(email='', action='GET'):
    if action == 'GET':
        return requests.get(UserServiceApiUrl.FORGOT_PASSWORD_API).status_code
    else:
        response = requests.post(url=UserServiceApiUrl.FORGOT_PASSWORD_API, data={"username": email})
        return response.status_code


def reset_password(token, password='', action='GET'):
    if action == 'GET':
        return requests.get(UserServiceApiUrl.RESET_PASSWORD_API % token).status_code
    else:
        response = requests.post(url=UserServiceApiUrl.RESET_PASSWORD_API % token, data={"password": password})
        return response.status_code


def user_api(access_token, user_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        if user_id:
            response = requests.get(url=UserServiceApiUrl.USER % user_id, headers=headers)
            return response.json(), response.status_code
        else:
            response = requests.get(url=UserServiceApiUrl.USERS, headers=headers)
            return response.json(), response.status_code
    elif action == 'DELETE':
        response = requests.delete(url=UserServiceApiUrl.USER % user_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=UserServiceApiUrl.USER % user_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=UserServiceApiUrl.USERS, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def domain_api(access_token, domain_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        url = UserServiceApiUrl.DOMAIN % domain_id if domain_id else UserServiceApiUrl.DOMAINS
        response = requests.get(url=url, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        url = UserServiceApiUrl.DOMAIN % domain_id if domain_id else UserServiceApiUrl.DOMAINS
        response = requests.delete(url=url, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=UserServiceApiUrl.DOMAIN % domain_id, headers=headers,
                                data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=UserServiceApiUrl.DOMAINS, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
