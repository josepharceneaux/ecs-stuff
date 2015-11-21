__author__ = 'ufarooqi'
import pytest
from werkzeug.security import gen_salt
from common_functions import *
from candidate_pool_service.common.models.candidate import Candidate
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPool, TalentPoolGroup


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
        token = Token.query.filter_by(access_token=admin_user_access_token).first()
        if token:
            token.delete()
    request.addfinalizer(tear_down)
    return admin_user_access_token


@pytest.fixture()
def domain_admin_access_token(request, domain_admin_user, sample_client):
    domain_admin_user_access_token = get_access_token(domain_admin_user, PASSWORD,
                                                      sample_client.client_id, sample_client.client_secret)

    def tear_down():
        token = Token.query.filter_by(access_token=domain_admin_user_access_token).first()
        if token:
            token.delete()
    request.addfinalizer(tear_down)
    return domain_admin_user_access_token


@pytest.fixture()
def group_admin_access_token(request, group_admin_user, sample_client):
    group_admin_user_access_token = get_access_token(group_admin_user, PASSWORD, sample_client.client_id,
                                                     sample_client.client_secret)

    def tear_down():
        token = Token.query.filter_by(access_token=group_admin_user_access_token).first()
        if token:
            token.delete()
    request.addfinalizer(tear_down)
    return group_admin_user_access_token


@pytest.fixture()
def manage_talent_pool_access_token(request, manage_talent_pool_user, sample_client):
    manage_talent_pool_user_access_token = get_access_token(manage_talent_pool_user, PASSWORD, sample_client.client_id,
                                                            sample_client.client_secret)

    def tear_down():
        token = Token.query.filter_by(access_token=manage_talent_pool_user_access_token).first()
        if token:
            token.delete()
    request.addfinalizer(tear_down)
    return manage_talent_pool_user_access_token


@pytest.fixture()
def sample_user(request, domain, first_group):
    user = create_test_user(domain.id, PASSWORD)
    UserGroup.add_users_to_group(first_group, [user.id])

    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def admin_user(request, domain_second, admin_role, second_group):
    user = create_test_user(domain_second.id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [admin_role])
    UserGroup.add_users_to_group(second_group, [user.id])

    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def domain_admin_user(request, domain, domain_admin_role, first_group):
    user = create_test_user(domain.id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [domain_admin_role])
    UserGroup.add_users_to_group(first_group, [user.id])

    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def group_admin_user(request, domain_second, group_admin_role, second_group):
    user = create_test_user(domain_second.id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [group_admin_role])
    UserGroup.add_users_to_group(second_group, [user.id])

    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def manage_talent_pool_user(request, domain, manage_talent_pool_role, first_group):
    user = create_test_user(domain.id, PASSWORD)
    UserScopedRoles.add_roles(user, True, [manage_talent_pool_role])
    UserGroup.add_users_to_group(first_group, [user.id])

    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
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
            try:
                db.session.delete(DomainRole.query.get(role))
                db.session.commit()
            except:
                db.session.rollback()
        request.addfinalizer(tear_down)
    return role


@pytest.fixture()
def group_admin_role(request):
    role = DomainRole.get_by_name('GROUP_ADMIN') or ''
    if not role:
        role = DomainRole.save('GROUP_ADMIN')
    else:
        role = role.id

        def tear_down():
            try:
                db.session.delete(DomainRole.query.get(role))
                db.session.commit()
            except:
                db.session.rollback()
        request.addfinalizer(tear_down)
    return role


@pytest.fixture()
def manage_talent_pool_role(request):
    role = DomainRole.get_by_name('CAN_MANAGE_TALENT_POOLS') or ''
    if not role:
        role = DomainRole.save('CAN_MANAGE_TALENT_POOLS')
    else:
        role = role.id

        def tear_down():
            try:
                db.session.delete(DomainRole.query.get(role))
                db.session.commit()
            except:
                db.session.rollback()
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
            try:
                db.session.delete(DomainRole.query.get(role))
                db.session.commit()
            except:
                db.session.rollback()
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
        try:
            db.session.delete(test_domain)
            db.session.commit()
        except:
            db.session.rollback()
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
        try:
            db.session.delete(test_domain)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return test_domain


@pytest.fixture()
def first_group(request, domain):
    user_group = UserGroup(name=gen_salt(20), domain_id=domain.id)
    db.session.add(user_group)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(user_group)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user_group


@pytest.fixture()
def second_group(request, domain_second):
    user_group = UserGroup(name=gen_salt(20), domain_id=domain_second.id)
    db.session.add(user_group)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(user_group)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user_group


@pytest.fixture()
def talent_pool(request, domain, first_group, admin_user):
    talent_pool = TalentPool(name=gen_salt(20), description='', domain_id=domain.id, owner_user_id=admin_user.id)
    db.session.add(talent_pool)
    db.session.commit()

    db.session.add(TalentPoolGroup(talent_pool_id=talent_pool.id, user_group_id=first_group.id))
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(talent_pool)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return talent_pool


@pytest.fixture()
def talent_pool_second(request, domain_second, admin_user):
    talent_pool = TalentPool(name=gen_salt(20), description='', domain_id=domain_second.id, owner_user_id=admin_user.id)
    db.session.add(talent_pool)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(talent_pool)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return talent_pool


@pytest.fixture()
def candidate_first(request):
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20))
    db.session.add(candidate)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(candidate)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture()
def candidate_second(request):
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20))
    db.session.add(candidate)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(candidate)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return candidate