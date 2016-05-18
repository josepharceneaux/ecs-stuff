import json
import random
import string
from urllib import urlencode

import pytest
import requests
from werkzeug.security import gen_salt
from auth_service.oauth import app
from auth_service.common.models.user import *
from auth_service.common.routes import AuthApiUrl, AuthApiUrlV2
from auth_service.common.utils.auth_utils import gettalent_generate_password_hash


class AuthServiceTestsContext:
    def __init__(self):
        self.email = ''
        self.password = ''
        self.client_id = ''
        self.client_secret = ''
        self.access_token = ''
        self.secret_key_id = ''
        self.test_domain = None

    def set_up(self):
        # Add test user in user DB
        random_email = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
        self.email = '%s.sample@example.com' % random_email
        self.password = ''.join(random.choice(string.ascii_letters + string.digits) for n in range(6))
        first_name = 'John'
        last_name = 'Sample'

        # Add test domain
        test_domain = Domain(
            name=gen_salt(20),
            expiration='0000-00-00 00:00:00'
        )
        db.session.add(test_domain)
        db.session.commit()
        self.test_domain = test_domain.get_id()

        test_user = User(
            email=self.email,
            password=gettalent_generate_password_hash(self.password),
            domain_id=self.test_domain,
            first_name=first_name,
            last_name=last_name,
            expiration=None
        )
        db.session.add(test_user)

        # Add test client in Client DB
        self.client_id = gen_salt(40)
        self.client_secret = gen_salt(50)
        test_client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        db.session.add(test_client)
        db.session.commit()

    def authorize_token(self):
        headers = {'Authorization': 'Bearer %s' % self.access_token}
        if self.secret_key_id:
            headers['X-Talent-Secret-Key-ID'] = self.secret_key_id
        response = requests.get(AuthApiUrl.AUTHORIZE, headers=headers)
        if response.status_code == 200:
            response_data = json.loads(response.text)
            return response.status_code, response_data.get('user_id') if response_data else ''
        else:
            return response.status_code, ''

    def authorize_token_v2(self):
        headers = {'Authorization': 'Bearer %s' % self.access_token, 'X-Talent-Secret-Key-ID': self.secret_key_id}
        response = requests.get(AuthApiUrlV2.AUTHORIZE, headers=headers)
        if response.status_code == 200:
            response_data = json.loads(response.text)
            return response.status_code, response_data.get('user_id') if response_data else ''
        else:
            return response.status_code, ''

    def token_handler(self, params, headers, refresh_token='', action='fetch'):
        params = params.copy()
        access_token = ''

        if action == 'fetch':
            params['username'] = self.email
            params['password'] = self.password
        elif action == 'refresh':
            params['refresh_token'] = refresh_token
            params['grant_type'] = 'refresh_token'
        elif action == 'revoke':
            params['grant_type'] = 'password'
            params['token'] = self.access_token
        else:
            raise Exception("%s is not a valid action" % action)

        headers['Origin'] = 'https://app.gettalent.com'  # To verify that CORS headers work
        response = requests.post(AuthApiUrl.TOKEN_REVOKE if action == 'revoke' else
                                 AuthApiUrl.TOKEN_CREATE, data=urlencode(params), headers=headers)
        db.session.commit()
        if action == 'revoke':
            return response.status_code
        json_response = json.loads(response.text)
        if json_response:
            access_token = json_response.get('access_token') or ''
            refresh_token = json_response.get('refresh_token') or ''

        return access_token, refresh_token, response.status_code

    def token_handler_v2(self, action='fetch'):

        headers = {'content-type': 'application/x-www-form-urlencoded', 'Origin': 'https://app.gettalent.com'}

        if action == 'fetch':
            params = {'username': self.email, 'password': self.password}
            response = requests.post(AuthApiUrlV2.TOKEN_CREATE, data=urlencode(params), headers=headers)
            json_response = json.loads(response.text)
            access_token = json_response.get('access_token', '') if json_response else ''
            secret_key_id = json_response.get('secret_key_id', '') if json_response else ''
            return access_token, secret_key_id, response.status_code
        elif action == 'refresh':
            headers = {'Authorization': 'Bearer %s' % self.access_token, 'X-Talent-Secret-Key-ID': self.secret_key_id}
            response = requests.post(AuthApiUrlV2.TOKEN_REFRESH, headers=headers)
            json_response = json.loads(response.text)
            access_token = json_response.get('access_token', '') if response else ''
            secret_key_id = json_response.get('secret_key_id', '') if response else ''
            return access_token, secret_key_id, response.status_code
        else:
            headers = {'Authorization': 'Bearer %s' % self.access_token, 'X-Talent-Secret-Key-ID': self.secret_key_id}
            response = requests.post(AuthApiUrlV2.TOKEN_REVOKE, headers=headers)
            return response.status_code


@pytest.fixture()
def app_context(request):
    context = AuthServiceTestsContext()
    context.set_up()

    def tear_down():
        token = Token.query.filter_by(access_token=context.access_token).first()
        client = Client.query.filter_by(client_id=context.client_id).first()
        user = User.query.filter_by(email=context.email).first()
        test_domain = Domain.query.get(context.test_domain)
        if token:
            db.session.delete(token)
        if client:
            db.session.delete(client)
        if user:
            db.session.delete(user)
        if test_domain:
            db.session.delete(test_domain)
        db.session.commit()

    request.addfinalizer(tear_down)
    return context


def test_auth_service_v2(app_context):

    # Fetch Bearer Token
    app_context.access_token, app_context.secret_key_id, status_code = app_context.token_handler_v2()
    assert status_code == 200

    # Authorize Bearer Token
    status_code, authorized_user_id = app_context.authorize_token_v2()
    assert status_code == 200

    # Refresh Bearer Token
    access_token, secret_key_id, status_code = app_context.token_handler_v2(action='refresh')
    assert status_code == 200

    # Authorize Old Bearer Token
    status_code, authorized_user_id = app_context.authorize_token_v2()
    assert status_code == 401

    # Authorize new bearer token
    app_context.access_token = access_token
    app_context.secret_key_id = secret_key_id
    status_code, authorized_user_id = app_context.authorize_token_v2()
    assert status_code == 200

    # Revoke a Bearer Token
    assert app_context.token_handler_v2(action='revoke') == 200

    # Authorize Revoked bearer token Bearer Token
    status_code, authorized_user_id = app_context.authorize_token_v2()
    assert status_code == 401


def test_auth_service_v1(app_context):

    headers = {'content-type': 'application/x-www-form-urlencoded'}
    params = {'grant_type': 'password', 'client_id': app_context.client_id, 'client_secret': app_context.client_secret}

    # Fetch Bearer Token
    app_context.access_token, refresh_token, status_code = app_context.token_handler(params, headers)
    assert status_code == 200 and Token.query.filter(Token.access_token == app_context.access_token
                                                     and Token.refresh_token == refresh_token).first()

    token = Token.query.filter_by(access_token=app_context.access_token).first()
    token.expires = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    db.session.commit()

    # Authorize an expired Bearer Token
    status_code, authorized_user_id = app_context.authorize_token()
    assert status_code == 401

    # Refresh Bearer Token
    app_context.access_token, refresh_token, status_code = app_context.token_handler(params, headers,
                                                                                     refresh_token, action='refresh')
    assert status_code == 200 and Token.query.filter(Token.access_token == app_context.access_token
                                                     and Token.refresh_token == refresh_token).first()

    # Authorize a Bearer Token
    user_id = User.query.filter_by(email=app_context.email).first().id
    status_code, authorized_user_id = app_context.authorize_token()
    assert status_code == 200 and authorized_user_id == user_id

    # Revoke a Bearer Token
    assert app_context.token_handler(params, headers, action='revoke') == 200

    # Authorize revoked bearer token
    status_code, authorized_user_id = app_context.authorize_token()
    assert status_code == 401


def test_health_check():
    import requests
    response = requests.get(AuthApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(AuthApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == 200
