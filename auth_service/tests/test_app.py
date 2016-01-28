import json
import random
import string
from urllib import urlencode

import pytest
import requests
from werkzeug.security import gen_salt
from auth_service.oauth import app
from auth_service.common.models.user import *
from auth_service.common.routes import AuthApiUrl
from auth_service.common.utils.auth_utils import gettalent_generate_password_hash

class AuthServiceTestsContext:
    def __init__(self):
        self.email = ''
        self.password = ''
        self.client_id = ''
        self.client_secret = ''
        self.access_token = ''
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
        response = requests.get(AuthApiUrl.AUTHORIZE, headers=headers)
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


def test_auth_service(app_context):
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    params = {'client_id': app_context.client_id, 'client_secret': app_context.client_secret, 'grant_type': 'password'}

    # Fetch Bearer Token
    app_context.access_token, refresh_token, status_code = app_context.token_handler(params, headers)
    assert status_code == 200 and Token.query.filter(Token.access_token == app_context.access_token
                                                     and Token.refresh_token == refresh_token).first()

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
