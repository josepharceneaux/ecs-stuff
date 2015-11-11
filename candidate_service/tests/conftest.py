__author__ = 'naveen'

import pytest
from werkzeug.security import gen_salt
from common_functions import *

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'
PASSWORD = gen_salt(20)


@pytest.fixture()
def sample_client(request):
    # Adding sample client credentials to Database
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    test_client = Client(
        client_id=client_id,
        client_secret=client_secret
    )
    db.session.add(test_client)
    db.session.commit()

    def tear_down():
        test_client.delete()
    request.addfinalizer(tear_down)
    return test_client


@pytest.fixture()
def access_token(request, sample_user, sample_client):
    sample_user_access_token = get_access_token(sample_user, PASSWORD, sample_client.client_id, sample_client.client_secret)

    def tear_down():
        Token.query.filter_by(access_token=sample_user_access_token).first().delete()
    request.addfinalizer(tear_down)
    return sample_user_access_token


@pytest.fixture()
def admin_access_token(request, admin_user, sample_client):
    admin_user_access_token = get_access_token(admin_user, PASSWORD, sample_client.client_id, sample_client.client_secret)

    def tear_down():
        Token.query.filter_by(access_token=admin_user_access_token).first().delete()
    request.addfinalizer(tear_down)
    return admin_user_access_token


@pytest.fixture()
def sample_user(request, domain_id):
    user = create_test_user(domain_id, PASSWORD)

    def tear_down():
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user.id


@pytest.fixture()
def admin_user(request, domain_id, domain_admin_role):
    user = create_test_user(domain_id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [domain_admin_role])
    user_scoped_role = UserScopedRoles.query.filter((UserScopedRoles.user_id == user.id)
                                                                & (UserScopedRoles.role_id == domain_admin_role)).first()

    def tear_down():
        db.session.delete(user_scoped_role)
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user.id


@pytest.fixture
def domain_admin_role(request):
    role = DomainRole.get_by_name('DOMAIN_ADMIN') or ''
    if not role:
        role = DomainRole.save('DOMAIN_ADMIN')

        def tear_down():
            db.session.delete(role)
            db.session.commit()
        request.addfinalizer(tear_down)
    return role.id


@pytest.fixture()
def domain_id(request):
    test_domain = Domain(
        name=gen_salt(20),
        expiration='0000-00-00 00:00:00'
    )
    db.session.add(test_domain)
    db.session.commit()

    def tear_down():
        db.session.delete(test_domain)
        db.session.commit()
    request.addfinalizer(tear_down)
    return test_domain.get_id()

