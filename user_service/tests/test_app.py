import pytest
from werkzeug.security import  gen_salt
from common_functions import *

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'
REVOKE_URL = OAUTH_ENDPOINT % 'oauth2/revoke'
AUTHORIZE_URL = OAUTH_ENDPOINT % 'oauth2/authorize'


@pytest.fixture()
def access_token(request, non_admin_user, admin_user):
    # Adding test client_Credentials to Database
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    test_client = Client(
        client_id=client_id,
        client_secret=client_secret
    )
    db.session.add(test_client)
    db.session.commit()

    non_admin_user_access_token = get_access_token(non_admin_user, client_id, client_secret)
    admin_user_access_token = get_access_token(admin_user, client_id, client_secret)

    def tear_down():
        db.session.delete(Token.query.filter_by(access_token=non_admin_user_access_token).first())
        db.session.delete(Token.query.filter_by(access_token=admin_user_access_token).first())
        db.session.delete(test_client)
        db.session.commit()
    request.addfinalizer(tear_down())

    return {'access_token': {'non_admin_user': non_admin_user_access_token, 'admin_user': admin_user_access_token}}


@pytest.fixture()
def non_admin_user(request, domain_id):
    user = create_test_user(domain_id)

    def tear_down():
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def admin_user(request, domain_id, domain_admin_role):
    role = DomainRole.get_by_name('ADMIN') or ''
    if not role:
        role = DomainRole.save(domain_id, 'ADMIN')
    user = create_test_user(domain_id)
    user_scoped_role = UserScopedRoles.add_roles(user.id, [domain_admin_role])

    def tear_down():
         db.session.delete(role)
        db.session.commit()
        db.session.delete(user)
        db.session.delete(user_scoped_role)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture
def domain_admin_role(request, domain_id):
    role = DomainRole.get_by_name('ADMIN') or ''
    if not role:
        role = DomainRole.save(domain_id, 'ADMIN')

        def tear_down():
            db.session.delete(role)
            db.session.commit()
        request.addfinalizer(tear_down)
    return role.id


@pytest.fixture()
def domain_id(request):
    test_domain = Domain(
        name=gen_salt(20)
    )
    db.session.add(test_domain)
    db.session.commit()

    def tear_down():
        db.session.delete(test_domain)
        db.session.commit()
    request.addfinalizer(tear_down)
    return test_domain.get_id()


@pytest.fixture()
def domain_roles(request, domain_id):
    test_role_first = gen_salt(20)
    test_role_first_id = DomainRole.save(test_role_first)
    test_role_second = gen_salt(20)
    test_role_second_id = DomainRole.save(test_role_second, domain_id)

    def tear_down():
        db.session.delete(DomainRole.query.get(test_role_first_id))
        db.session.delete(DomainRole.query.get(test_role_second_id))
    request.addfinalizer(tear_down)
    return {'test_roles': [test_role_first, test_role_second]}


def test_user_scoped_roles(access_token):

    # Add roles to existing user
    assert user_scoped_roles(token=access_token, action="POST") == 200

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

