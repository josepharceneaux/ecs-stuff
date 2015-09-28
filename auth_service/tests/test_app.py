import pytest
import json
from auth_service.oauth import app, db, gt_oauth
from werkzeug.security import generate_password_hash, gen_salt
from models.user import *
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
        self.test_domain = None
        self.test_role_first = ""
        self.test_role_second = ""

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
            expiration=None
        )
        db.session.add(test_domain)
        db.session.commit()
        self.test_domain = test_domain.get_id()

        test_user = User(
            email=self.email,
            password=generate_password_hash(self.password, method='pbkdf2:sha512'),
            domainId=self.test_domain,
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

        # Add two test roles
        self.test_role_first = gen_salt(20)
        DomainRole.save(self.test_domain, self.test_role_first)
        self.test_role_second = gen_salt(20)
        DomainRole.save(self.test_domain, self.test_role_second)

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

    def test_roles_of_user(self, action="GET", false_case=False):
        headers = {'Authorization': 'Bearer %s' % self.access_token}
        if action == "GET":
            response = json.loads(self.app.get('/users/%s/roles' % self.oauth._usergetter(self.email, self.password)
                                               .get_id(), headers=headers).data)
            return response.get('roles')
        elif action == "POST":
            headers['content-type'] = 'application/json'
            test_role_first = DomainRole.get_by_name(self.test_role_first)
            test_role_second = DomainRole.get_by_name(self.test_role_second)
            if false_case:
                data = {'roles': [int(test_role_second.id) + 1]}
            else:
                data = {'roles': [self.test_role_first, test_role_second.id]}
            response = self.app.post('/users/%s/roles' % self.oauth._usergetter(self.email, self.password).get_id(),
                                     data=json.dumps(data), headers=headers)
            return response.status_code
        elif action == "DELETE":
            headers['content-type'] = 'application/json'
            data = {'roles': [self.test_role_first, DomainRole.get_by_name(self.test_role_second).id]}
            response = self.app.delete('/users/%s/roles' % self.oauth._usergetter(self.email, self.password).get_id(),
                                       data=json.dumps(data), headers=headers)
            return response.status_code

    def get_roles_of_domain(self):
        headers = {'Authorization': 'Bearer %s' % self.access_token}
        response = json.loads(self.app.get('/domain/%s/roles' % self.test_domain, headers=headers).data)
        domain_roles = response.get('roles') or []
        return [domain_role.get('name') for domain_role in domain_roles]

    def verify_user_scoped_role(self, role):
        user_id = self.oauth._usergetter(self.email, self.password).get_id()
        import urllib
        response = json.loads(self.app.get("/roles/verify", query_string=urllib.urlencode({"role": role,
                                                                                           "user_id": user_id})).data)
        return response.get('success')

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
        test_role_first = DomainRole.get_by_name(context.test_role_first) or None
        test_role_second = DomainRole.get_by_name(context.test_role_second) or None
        test_domain = Domain.query.get(context.test_domain) or None
        if token:
            db.session.delete(token)
        if client:
            db.session.delete(client)
        if user:
            user_scoped_roles = UserScopedRoles.query.filter_by(userId=user.id).all()
            for user_scoped_role in user_scoped_roles:
                db.session.delete(user_scoped_role)
            db.session.commit()
            db.session.delete(user)
        if test_role_first:
            db.session.delete(test_role_first)
        if test_role_second:
            db.session.delete(test_role_second)
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

    # Add roles to existing user
    assert app_context.test_roles_of_user(action="POST") == 200

    # Check if roles has been added successfully in existing user
    assert app_context.test_roles_of_user() == [DomainRole.get_by_name(app_context.test_role_first).id,
                                                DomainRole.get_by_name(app_context.test_role_second).id]

    # Add a false role to existing user
    assert app_context.test_roles_of_user(action="POST", false_case=True) != 200

    # verify a user role
    assert app_context.verify_user_scoped_role(app_context.test_role_first)
    assert app_context.verify_user_scoped_role(app_context.test_role_second)

    # Get all roles of a domain
    assert app_context.get_roles_of_domain() == [app_context.test_role_first, app_context.test_role_second]

    # Delete roles from a user
    assert app_context.test_roles_of_user(action="DELETE") == 200

    # Check if roles have been deleted successfully from a user
    assert not app_context.test_roles_of_user()

    # Revoke a Bearer Token
    assert app_context.token_handler(params, headers, action='revoke') == 200

    # Authorize revoked bearer token
    status_code, authorized_user_id = app_context.authorize_token()
    assert status_code == 401

