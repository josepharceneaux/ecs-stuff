import pytest
from werkzeug.security import gen_salt
from user_service.user_app import app
from common_functions import *

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'

APP = app.test_client()


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
    request.addfinalizer(tear_down)

    return {'non_admin_user': non_admin_user_access_token, 'admin_user': admin_user_access_token}


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
    user = create_test_user(domain_id)
    user_scoped_role = UserScopedRoles.add_roles(user.id, [domain_admin_role])

    def tear_down():
        db.session.delete(user_scoped_role)
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture
def domain_admin_role(request):
    role = DomainRole.get_by_name('ADMIN') or ''
    if not role:
        role = DomainRole.save('ADMIN')

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


@pytest.fixture()
def domain_roles(request, domain_id):
    test_role_first = gen_salt(20)
    test_role_first_id = DomainRole.save(test_role_first, domain_id)
    test_role_second = gen_salt(20)
    test_role_second_id = DomainRole.save(test_role_second)

    def tear_down():
        db.session.delete(DomainRole.query.get(test_role_first_id))
        db.session.delete(DomainRole.query.get(test_role_second_id))
    request.addfinalizer(tear_down)
    return {'test_roles': [test_role_first, test_role_second]}


@pytest.fixture()
def user_groups(request, domain_id):
    test_group_first = gen_salt(20)
    test_group_first_id = UserGroups.save(domain_id, test_group_first, "It's first test group")
    test_group_second = gen_salt(20)
    test_group_second_id = UserGroups.save(domain_id, test_group_second, "It's second test group")

    def tear_down():
        db.session.delete(UserGroups.query.get(test_group_first_id))
        db.session.delete(UserGroups.query.get(test_group_second_id))
    request.addfinalizer(tear_down)
    return {'test_groups': [test_group_first, test_group_second]}


def test_user_scoped_roles(access_token, non_admin_user, domain_roles, domain_id):

    # Add roles to existing user
    assert user_scoped_roles(access_token=access_token['admin_user'], user_id=non_admin_user.id, action="POST",
                             test_roles=domain_roles['test_roles']) == 200

    # Check if roles has been added successfully in existing user
    assert user_scoped_roles(access_token=access_token['admin_user'], user_id=non_admin_user.id) == \
           [DomainRole.get_by_name(domain_roles['test_roles'][0]).id, DomainRole.get_by_name(domain_roles['test_roles'][1]).id]

    # Add a false role to existing user
    assert user_scoped_roles(access_token=access_token['admin_user'], user_id=non_admin_user.id, action="POST",
                             test_roles=domain_roles['test_roles'], false_case=True) != 200

    # verify a user role
    assert verify_user_scoped_role(non_admin_user, domain_roles['test_roles'][0])
    assert verify_user_scoped_role(non_admin_user, domain_roles['test_roles'][1])
    #
    # Get all roles of a domain
    assert get_roles_of_domain(access_token=access_token['admin_user'], domain_id=domain_id) == [domain_roles['test_roles'][0]]

    # Get all roles of a domain using non-admin user
    assert get_roles_of_domain(access_token=access_token['non_admin_user'], domain_id=domain_id) == 401

    # Delete roles from a user
    assert user_scoped_roles(access_token=access_token['admin_user'], user_id=non_admin_user.id, action="DELETE",
                             test_roles=domain_roles['test_roles']) == 200
    #
    # Check if roles have been deleted successfully from a user
    assert not user_scoped_roles(access_token=access_token['admin_user'], user_id=non_admin_user.id)

def test_user_groups(access_token, non_admin_user, domain_groups):



