__author__ = 'ufarooqi'
import pytest
from werkzeug.security import gen_salt
from common_functions import *
from user_service.common.models.misc import Culture


PASSWORD = gen_salt(20)
CHANGED_PASSWORD = gen_salt(20)


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
        token = Token.query.filter_by(access_token=sample_user_access_token).first()
        if token:
            token.delete()
    request.addfinalizer(tear_down)
    return sample_user_access_token


@pytest.fixture()
def admin_access_token(request, admin_user, sample_client):
    admin_user_access_token = get_access_token(admin_user, PASSWORD, sample_client.client_id, sample_client.client_secret)

    def tear_down():
        admin_user_token = Token.query.filter_by(access_token=admin_user_access_token).first()
        if admin_user_token:
            admin_user_token.delete()
    request.addfinalizer(tear_down)
    return admin_user_access_token


@pytest.fixture()
def domain_admin_access_token(request, domain_admin_user, sample_client):
    domain_admin_user_access_token = get_access_token(domain_admin_user, PASSWORD,
                                                      sample_client.client_id, sample_client.client_secret)

    def tear_down():
        admin_user_token = Token.query.filter_by(access_token=domain_admin_user_access_token).first()
        if admin_user_token:
            admin_user_token.delete()
    request.addfinalizer(tear_down)
    return domain_admin_user_access_token


@pytest.fixture()
def sample_user(request, domain):
    user = create_test_user(domain.id, PASSWORD)

    def tear_down():
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def admin_user(request, domain_second, admin_role):
    user = create_test_user(domain_second.id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [admin_role])
    user_scoped_role = UserScopedRoles.query.filter((UserScopedRoles.user_id == user.id)
                                                                & (UserScopedRoles.role_id == admin_role)).first()

    def tear_down():
        db.session.delete(user_scoped_role)
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def domain_admin_user(request, domain, domain_admin_role):
    user = create_test_user(domain.id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [domain_admin_role])
    user_scoped_role = UserScopedRoles.query.filter((UserScopedRoles.user_id == user.id)
                                                                & (UserScopedRoles.role_id == domain_admin_role)).first()

    def tear_down():
        db.session.delete(user_scoped_role)
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def domain_admin_role(request):
    role = DomainRole.get_by_name('DOMAIN_ADMIN') or ''
    if not role:
        role = DomainRole.save('DOMAIN_ADMIN')
    else:
        role = role.id

        def tear_down():
            db.session.delete(DomainRole.query.get(role))
            db.session.commit()
        request.addfinalizer(tear_down)
    return role


@pytest.fixture()
def admin_role(request):
    role = DomainRole.get_by_name('ADMIN') or ''
    if not role:
        role = DomainRole.save('ADMIN')
    else:
        role = role.id

        def tear_down():
            db.session.delete(DomainRole.query.get(role))
            db.session.commit()
        request.addfinalizer(tear_down)
    return role


@pytest.fixture()
def domain(request):
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
    return test_domain


@pytest.fixture()
def domain_second(request):
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
    return test_domain


@pytest.fixture()
def domain_roles(request, domain):
    test_role_first = gen_salt(20)
    test_role_first_id = DomainRole.save(test_role_first, domain.id)
    test_role_second = gen_salt(20)
    test_role_second_id = DomainRole.save(test_role_second, domain.id)

    def tear_down():
        db.session.delete(DomainRole.query.get(test_role_first_id))
        db.session.delete(DomainRole.query.get(test_role_second_id))
        db.session.commit()
    request.addfinalizer(tear_down)
    return {'test_roles': [test_role_first, test_role_second]}


@pytest.fixture()
def group_names():
    return {'test_groups': [gen_salt(20), gen_salt(20)]}


@pytest.fixture()
def culture(request):
    culture_object = Culture(description=gen_salt(10), code=100)
    db.session.add(culture_object)
    db.session.commit()

    def tear_down():
        db.session.delete(culture_object)
        db.session.commit()
    request.addfinalizer(tear_down())

    return culture_object
