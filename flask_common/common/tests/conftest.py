# Standard Library
from datetime import datetime
import random, string, uuid

# Third Party
import json
import pytest, requests
from faker import Faker
from werkzeug.security import gen_salt
from ..models.candidate import Candidate
from ..models.user import UserGroup, DomainRole
from auth_utilities import get_access_token, create_test_user, get_or_create

# Application Specific
from ..models.db import db
from ..models.user import (Client, Domain, User, Token)
from ..models.talent_pools_pipelines import (TalentPool, TalentPoolGroup, TalentPipeline)
from ..models.misc import (Culture, Organization, AreaOfInterest, CustomField)


fake = Faker()
ISO_FORMAT = '%Y-%m-%d %H:%M'
USER_HASHED_PASSWORD = 'pbkdf2(1000,64,sha512)$a97efdd8d6b0bf7f$55de0d7bafb29a88e7596542aa927ac0e1fbc30e94db2c5215851c72294ebe01fb6461b27f0c01b9bd7d3ce4a180707b6652ba2334c7a2b0fcb93c946aa8b4ec'
USER_PASSWORD = 'Talent15'

# TODO: Above fixed passwords should be removed and random passwords should be used
PASSWORD = gen_salt(20)
CHANGED_PASSWORD = gen_salt(20)


class UserAuthentication:
    def __init__(self, db):
        self.db = db
        self.client_id = str(uuid.uuid4())[0:8]     # can be any arbitrary string
        self.client_secret = str(uuid.uuid4())[0:8] # can be any arbitrary string
        self.new_client = Client(client_id=self.client_id, client_secret=self.client_secret)

    def get_auth_token(self, user_row, get_bearer_token=False):
        """ Function will add new_client to the database
        :param user:    user-row
        :return:        {'client_id': '01a14510', 'client_secret': '04077ead'}
        """
        self.db.session.add(self.new_client)
        self.db.session.commit()
        # will return return access_token, refresh_token, user_id, token_type, and expiration date + time
        if get_bearer_token:
            return get_token(user_login_credentials=dict(
                client_id=self.client_id, client_secret=self.client_secret, user_row=user_row
            ))
        return dict(client_id=self.client_id, client_secret=self.client_secret, user_row=user_row)

    def get_auth_credentials_to_revoke_token(self, user_row, auto_revoke=False):
        self.db.session.commit()
        token = Token.query.filter_by(user_id=user_row.id).first()
        # if auto_revoke is set to True, function will post to /oauth2/revoke and assert its success
        if auto_revoke:
            return revoke_token(user_logout_credentials=dict(
                token=token, client_id=self.client_id, client_secret=self.client_secret, user=user_row
            ))
        return dict(token=token, client_id=self.client_id, client_secret=self.client_secret,
                    grand_type='password')

    def refresh_token(self, user_row):
        token = Token.query.filter_by(user_id=user_row.id).first()
        return dict(grand_type='refresh_token', token_row=token)


@pytest.fixture()
def user_auth():
    return UserAuthentication(db=db)


def get_token(user_login_credentials):
    data = {'client_id': user_login_credentials['client_id'],
            'client_secret': user_login_credentials['client_secret'],
            'username': user_login_credentials['user_row'].email,
            'password': 'Talent15',
            'grant_type':'password'}
    resp = requests.post('http://localhost:8001/v1/oauth2/token', data=data)
    assert resp.status_code == 200
    return resp.json()


def revoke_token(user_logout_credentials):
    access_token = user_logout_credentials['token'].access_token
    revoke_data = {'client_id': user_logout_credentials['client_id'],
                   'client_secret': user_logout_credentials['client_secret'],
                   'token': access_token,
                   'grant_type': 'password'}
    resp = requests.post('http://localhost:8001/v1/oauth2/revoke', data=revoke_data)
    assert resp.status_code == 200
    return


@pytest.fixture()
def sample_user(test_domain, request):
    user = User.add_test_user(db.session, test_domain.id, 'Talent15')
    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def sample_user_2(test_domain, request):
    user = User.add_test_user(db.session, test_domain.id, 'Talent15')
    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def user_from_diff_domain(test_domain_2, request):
    user = User.add_test_user(db.session, test_domain_2.id, 'Talent15')

    def tear_down():
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def test_domain(request):
    domain = Domain(name=gen_salt(20), expiration='0000-00-00 00:00:00')
    db.session.add(domain)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(domain)
            db.session.commit()
        except Exception:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return domain


@pytest.fixture()
def test_domain_2(request):
    domain = Domain(name=gen_salt(20), expiration='0000-00-00 00:00:00')
    db.session.add(domain)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(domain)
            db.session.commit()
        except Exception:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return domain


@pytest.fixture(autouse=True)
def test_culture(request):
    culture_attrs = dict(description='Foo {}'.format(randomword(12)), code=randomword(5))
    test_culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(test_culture)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_culture)
            db.session.commit()
        except Exception:
            db.session.rollback()
            pass

    request.addfinalizer(fin)
    return test_culture


@pytest.fixture(autouse=True)
def test_org(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(randomword(8)))
    test_org, created = get_or_create(session=db.session, model=Organization, **org_attrs)
    if created:
        db.session.add(test_org)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_org)
            db.session.commit()
        except Exception:
            db.session.rollback()
            pass

    request.addfinalizer(fin)
    return test_org


def areas_of_interest_for_domain(domain_id):
    """
    Function will add AreaOfInterest to user's domain
    :type user: User
    :rtype      [AreaOfInterest]
    """
    areas_of_interest = [{'name': fake.job()}, {'name': fake.job()}]
    for area_of_interest in areas_of_interest:
        db.session.add(AreaOfInterest(domain_id=domain_id, name=area_of_interest['name']))

    db.session.commit()
    return AreaOfInterest.get_domain_areas_of_interest(domain_id=domain_id)


def custom_field_for_domain(domain_id):
    """
    Function will add CustomField to user's domain
    :type user: User
    :rtype:  [CustomField]
    """
    import datetime
    custom_fields = [{'name': fake.word(), 'type': 'string'}, {'name': fake.word(), 'type': 'string'}]
    for custom_field in custom_fields:
        db.session.add(CustomField(domain_id=domain_id, name=custom_field['name'],
                                   type=custom_field['type'], added_time=datetime.datetime.now()))
    db.session.commit()
    return CustomField.get_domain_custom_fields(domain_id=domain_id)


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
def access_token_first(user_first, sample_client):
    return get_access_token(user_first, PASSWORD, sample_client.client_id, sample_client.client_secret)


@pytest.fixture()
def access_token_second(user_second, sample_client):
    return get_access_token(user_second, PASSWORD, sample_client.client_id, sample_client.client_secret)


@pytest.fixture()
def user_first(request, domain_first, first_group):
    user = create_test_user(db.session, domain_first.id, PASSWORD)
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
def user_second(request, domain_second, second_group):
    user = create_test_user(db.session, domain_second.id, PASSWORD)
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
def domain_first(request):
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
def domain_roles(request):
    test_role_first = gen_salt(20)
    test_role_first_id = DomainRole.save(test_role_first)
    test_role_second = gen_salt(20)
    test_role_second_id = DomainRole.save(test_role_second)

    def tear_down():
        try:
            db.session.delete(DomainRole.query.get(test_role_first_id))
            db.session.delete(DomainRole.query.get(test_role_second_id))
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return {'test_roles': [test_role_first, test_role_second]}


@pytest.fixture()
def first_group(request, domain_first):
    user_group = UserGroup(name=gen_salt(20), domain_id=domain_first.id)
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
def talent_pool(request, domain_first, first_group, user_first):
    talent_pool = TalentPool(name=gen_salt(20), description='', domain_id=domain_first.id, owner_user_id=user_first.id)
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
def talent_pool_second(request, domain_second, user_second):
    talent_pool = TalentPool(name=gen_salt(20), description='', domain_id=domain_second.id, owner_user_id=user_second.id)
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
def talent_pipeline(request, user_first, talent_pool):
    search_params = {
        "skills": "Python",
        "minimum_years_experience": "4",
        "location": "California"
    }
    talent_pipeline = TalentPipeline(name=gen_salt(6), description=gen_salt(15), positions=2,
                                     date_needed=datetime.utcnow().isoformat(sep=' '), owner_user_id=user_first.id,
                                     talent_pool_id=talent_pool.id, search_params=json.dumps(search_params))
    db.session.add(talent_pipeline)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(talent_pipeline)
            db.session.commit()
        except:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return talent_pipeline


@pytest.fixture()
def candidate_first(request, user_first):
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20), user_id=user_first.id)
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
def candidate_second(request, user_first):
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20), user_id=user_first.id)
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


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))
