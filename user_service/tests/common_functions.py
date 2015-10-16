__author__ = 'ufarooqi'
import random
import string
from werkzeug.security import generate_password_hash
from user_service.common.models.user import *
import requests
import json

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'

USER_SERVICE_ENDPOINT = 'http://127.0.0.1:8004/%s'
USER_ROLES = USER_SERVICE_ENDPOINT % 'users/%s/roles'
USER_ROLES_VERIFY = USER_SERVICE_ENDPOINT % 'roles/verify'
USER_DOMAIN_ROLES = USER_SERVICE_ENDPOINT % 'domain/%s/roles'


def create_test_user(domain_id):
    random_email = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
    email = '%s.sample@example.com' % random_email
    password = ''.join(random.choice(string.ascii_letters + string.digits) for n in range(6))
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
    # Store original value of password to user so that It can be used for getting Auth Token
    test_user.decoded_password = password
    return test_user


def get_access_token(user, client_id, client_secret):
    params = dict(grant_type="password", username=user.email, password=user.decoded_password)
    auth_service_token_response = requests.post(TOKEN_URL,
                                                params=params, auth=(client_id, client_secret)).json()
    if not (auth_service_token_response.get(u'access_token') and auth_service_token_response.get(u'refresh_token')):
        raise Exception("Either Access Token or Refresh Token is missing")
    else:
        return Token.query.filter_by(access_token=auth_service_token_response.get(u'access_token'))


def user_scoped_roles(token, test_role_first=None, test_role_second=None, action="GET", false_case=False):
    headers = {'Authorization': 'Bearer %s' % token.access_token}
    if action == "GET":
        response = json.loads(requests.get(USER_ROLES % token.user_id, headers=headers).data)
        return response.get('roles')
    elif action == "POST":
        headers['content-type'] = 'application/json'
        test_role_first = DomainRole.get_by_name(test_role_first)
        test_role_second = DomainRole.get_by_name(test_role_second)
        if false_case:
            data = {'roles': [int(test_role_second.id) + 1]}
        else:
            data = {'roles': [test_role_first, test_role_second.id]}
        response = requests.post(USER_ROLES % token.user_id, headers=headers, data=json.dumps(data))
        return response.status_code
    elif action == "DELETE":
        headers['content-type'] = 'application/json'
        data = {'roles': [test_role_first, DomainRole.get_by_name(test_role_second).id]}
        response = requests.delete(USER_ROLES % token.user_id, headers=headers, data=json.dumps(data))
        return response.status_code


def get_roles_of_domain(token):
    headers = {'Authorization': 'Bearer %s' % token.access_token}
    domain_id = User.query.get(token.user_id).domain_id
    response = json.loads(requests.get(USER_DOMAIN_ROLES % domain_id, headers=headers).data)
    domain_roles = response.get('roles') or []
    return [domain_role.get('name') for domain_role in domain_roles]


def verify_user_scoped_role(user, role):
    user_id = user.get_id()
    import urllib
    response = json.loads(requests.get(USER_ROLES_VERIFY, query_string=urllib.urlencode({"role": role,
                                                                                         "user_id": user_id})).data)
    return response.get('success')
