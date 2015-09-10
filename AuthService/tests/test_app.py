import pytest
import json
from oauth import app, db, gt_oauth
from werkzeug.security import generate_password_hash, gen_salt
from oauth.models import User, Client, Token
import random, string
from urllib import urlencode

TOKEN_URL = '/oauth2/token'
REVOKE_URL = '/oauth2/revoke'
AUTHORIZE_URL = '/oauth2/authorize'


class AuthServiceTestsContext:
    def __init__(self):
        self.app = app.test_client()
        self.oauth = gt_oauth
        self.email = ''
        self.password = ''
        self.client_id = ''
        self.client_secret = ''
        self.access_token = ''

    def set_up(self):
        # Add test user in user DB
        random_email = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
        self.email = '%s.sample@example.com' % random_email
        self.password = ''.join(random.choice(string.ascii_letters + string.digits) for n in range(6))
        first_name = 'John'
        last_name = 'Sample'

        test_user = User(
            email=self.email,
            password=generate_password_hash(self.password, method='pbkdf2:sha512'),
            domainId=1,
            firstName=first_name,
            lastName=last_name,
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
        response = self.app.get(AUTHORIZE_URL, headers=headers)
        response_data = self.json_response(response.data)
        return response.status_code, response_data.get('user_id') if response_data else ''

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

        response = self.app.post(REVOKE_URL if action == 'revoke' else TOKEN_URL, data=urlencode(params),
                                 headers=headers)
        if action == 'revoke':
            return response.status_code
        json_response = self.json_response(response.data)
        if json_response:
            access_token = json_response.get('access_token') or ''
            refresh_token = json_response.get('refresh_token') or ''

        return access_token, refresh_token, response.status_code

    @staticmethod
    def json_response(data):
        try:
            return json.loads(data)
        except Exception:
            return None


@pytest.fixture()
def app_context(request):
    context = AuthServiceTestsContext()
    context.set_up()

    def tear_down():
        token = context.oauth._tokengetter(access_token=context.access_token) or None
        client = context.oauth._clientgetter(context.client_id) or None
        user = context.oauth._usergetter(context.email, context.password) or None
        if token:
            db.session.delete(token)
        if client:
            db.session.delete(client)
        if user:
            db.session.delete(user)
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
