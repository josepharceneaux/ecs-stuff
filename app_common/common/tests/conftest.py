# Standard Library
import random
import requests
import string
import uuid
from datetime import datetime

# Third Party
import json
import pytest
from faker import Faker
from werkzeug.security import gen_salt

from ..models.candidate import Candidate
from ..models.user import UserGroup, DomainRole
from auth_utilities import get_access_token, get_or_create
from ..utils.handy_functions import JSON_CONTENT_TYPE_HEADER

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
        self.client_id = str(uuid.uuid4())[0:8]  # can be any arbitrary string
        self.client_secret = str(uuid.uuid4())[0:8]  # can be any arbitrary string
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
            'grant_type': 'password'}
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
def user_from_diff_domain(test_domain_2, second_group):
    """
    Fixture creates a user in domain_2
    """
    user = User.add_test_user(db.session, USER_PASSWORD, test_domain_2.id, second_group.id)
    return user


@pytest.fixture(autouse=True)
def test_domain():
    domain = Domain.add_test_domain(db.session)
    return domain


@pytest.fixture()
def test_domain_2():
    domain = Domain(name=gen_salt(20), expiration='0000-00-00 00:00:00')
    db.session.add(domain)
    db.session.commit()
    return domain


@pytest.fixture()
def test_culture():
    culture_attributes = dict(description='Foo {}'.format(randomword(12)), code=randomword(5))
    culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attributes)
    if created:
        db.session.add(culture)
        db.session.commit()

    return culture


@pytest.fixture()
def test_org():
    organization_attributes = dict(name='Rocket League All Stars - {}'.format(randomword(8)))
    organization, created = get_or_create(session=db.session, model=Organization, **organization_attributes)
    if created:
        db.session.add(organization)
        db.session.commit()

    return organization


@pytest.fixture()
def domain_aoi(domain_first):
    """Will add two areas-of-interest to domain
    :rtype:  list[AreaOfInterest]
    """
    areas_of_interest = [{'name': fake.job().lower()}, {'name': fake.job().lower()}]
    for area_of_interest in areas_of_interest:
        db.session.add(AreaOfInterest(domain_id=domain_first.id, name=area_of_interest['name']))

    db.session.commit()
    return AreaOfInterest.get_domain_areas_of_interest(domain_id=domain_first.id)


@pytest.fixture()
def domain_custom_fields(domain_first):
    """
    Will add custom fields to domain
    :rtype:  list[CustomField]
    """
    custom_fields = [{'name': fake.word(), 'type': 'string'}, {'name': fake.word(), 'type': 'string'}]
    for custom_field in custom_fields:
        db.session.add(CustomField(domain_id=domain_first.id, name=custom_field['name'],
                                   type=custom_field['type'], added_time=datetime.now()))
    db.session.commit()
    return CustomField.get_domain_custom_fields(domain_id=domain_first.id)


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
    return test_client


@pytest.fixture()
def access_token_first(user_first, sample_client):
    return get_access_token(user_first, PASSWORD, sample_client.client_id, sample_client.client_secret)


@pytest.fixture()
def access_token_second(user_second, sample_client):
    return get_access_token(user_second, PASSWORD, sample_client.client_id, sample_client.client_secret)


@pytest.fixture()
def access_token_same(user_same_domain, sample_client):
    return get_access_token(user_same_domain, PASSWORD, sample_client.client_id,
                            sample_client.client_secret)


@pytest.fixture()
def access_token_other(user_from_diff_domain, sample_client):
    """
    This returns the access token for user_from_diff_domain. We need this to create a resource
    e.g. email-campaign for some user in other domain and test the functionality of API.
    :param user_from_diff_domain: Fixture for user in some other domain
    :param sample_client: Fixture of `client` used in tests
    :return: access_token for given user
    :rtype: str
    """
    return get_access_token(user_from_diff_domain, USER_PASSWORD, sample_client.client_id,
                            sample_client.client_secret)


@pytest.fixture()
def user_first(domain_first, first_group):
    """
    Fixture creates a user in domain_first
    """
    user = User.add_test_user(db.session, PASSWORD, domain_first.id, first_group.id)
    return user


@pytest.fixture()
def user_same_domain(domain_first, first_group):
    """
    Fixture creates a user in domain_first
    """
    user = User.add_test_user(db.session, PASSWORD, domain_first.id, first_group.id)
    return user


@pytest.fixture()
def user_second(domain_second, second_group):
    """
    Fixture creates a user in domain_second
    """
    user = User.add_test_user(db.session, PASSWORD, domain_second.id, second_group.id)
    return user


@pytest.fixture()
def domain_first():
    domain = Domain.add_test_domain(session=db.session)
    return domain


@pytest.fixture()
def domain_second():
    domain = Domain(name=gen_salt(20), expiration='0000-00-00 00:00:00')
    db.session.add(domain)
    db.session.commit()
    return domain


@pytest.fixture()
def domain_roles():
    test_role_first = gen_salt(20)
    DomainRole.save(test_role_first)
    test_role_second = gen_salt(20)
    DomainRole.save(test_role_second)

    return {'test_roles': [test_role_first, test_role_second]}


@pytest.fixture()
def first_group(domain_first):
    """
    Fixture adds a group in domain_first
    """
    user_group = UserGroup(name=gen_salt(20), domain_id=domain_first.id)
    db.session.add(user_group)
    db.session.commit()
    return user_group


@pytest.fixture()
def second_group(domain_second):
    """
    Fixture adds a group in domain_second
    """
    user_group = UserGroup(name=gen_salt(20), domain_id=domain_second.id)
    db.session.add(user_group)
    db.session.commit()
    return user_group


@pytest.fixture()
def sample_user(domain_first, first_group):
    """
    Fixture adds a user in domain_first
    """
    user = User.add_test_user(db.session, USER_PASSWORD, domain_first.id, first_group.id)
    return user


@pytest.fixture()
def sample_user_2(domain_first, first_group):
    """
    Fixture adds a user in domain_first
    """
    user = User.add_test_user(db.session, USER_PASSWORD, domain_first.id, first_group.id)
    return user


@pytest.fixture()
def talent_pool(domain_first, first_group, user_first):
    """
    Fixture adds a talent pool in domain_first
    """
    tp = TalentPool(name=gen_salt(20), description='', domain_id=domain_first.id, user_id=user_first.id)
    db.session.add(tp)
    db.session.commit()

    db.session.add(TalentPoolGroup(talent_pool_id=tp.id, user_group_id=first_group.id))
    db.session.commit()

    return tp

@pytest.fixture()
def talent_pool_sample(domain_first, first_group, sample_user):
    """
    Fixture adds a talent pool in domain_first
    """
    tp = TalentPool(name=gen_salt(20), description='', domain_id=domain_first.id, user_id=sample_user.id)
    db.session.add(tp)
    db.session.commit()

    db.session.add(TalentPoolGroup(talent_pool_id=tp.id, user_group_id=first_group.id))
    db.session.commit()

    return tp


@pytest.fixture()
def talent_pool_second(domain_second, second_group, user_second):
    """
    Fixture adds talent pool to domain_second
    """
    tp = TalentPool(name=gen_salt(20), description='', domain_id=domain_second.id, user_id=user_second.id)
    db.session.add(tp)
    db.session.commit()

    db.session.add(TalentPoolGroup(talent_pool_id=tp.id, user_group_id=second_group.id))
    db.session.commit()

    return tp


@pytest.fixture()
def talent_pool_other(test_domain_2, second_group, user_from_diff_domain):
    """
    Fixture adds talent pool to domain_2
    """
    tp = TalentPool(name=gen_salt(20), description='', domain_id=test_domain_2.id, user_id=user_from_diff_domain.id)
    db.session.add(tp)
    db.session.commit()

    db.session.add(TalentPoolGroup(talent_pool_id=tp.id, user_group_id=second_group.id))
    db.session.commit()

    return tp


@pytest.fixture()
def talent_pipeline(user_first, talent_pool):
    """
    Fixture adds talent pipeline
    """
    talent_pipeline = TalentPipeline(name=gen_salt(6), description=gen_salt(15), positions=2,
                                     date_needed=datetime.utcnow().isoformat(sep=' '), user_id=user_first.id,
                                     talent_pool_id=talent_pool.id)
    db.session.add(talent_pipeline)
    db.session.commit()

    return talent_pipeline


@pytest.fixture()
def talent_pipeline_other(user_from_diff_domain, talent_pool_other):
    search_params = {
        "skills": "Python",
        "minimum_years_experience": "4",
        "location": "California"
    }
    talent_pipeline = TalentPipeline(name=gen_salt(6), description=gen_salt(15), positions=2,
                                     date_needed=datetime.utcnow().isoformat(sep=' '),
                                     user_id=user_from_diff_domain.id,
                                     talent_pool_id=talent_pool_other.id, search_params=json.dumps(search_params))
    db.session.add(talent_pipeline)
    db.session.commit()

    return talent_pipeline


@pytest.fixture()
def candidate_first(user_first):
    """
    Fixture will create a candidate in user_first's domain
    :rtype: Candidate
    """
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20), user_id=user_first.id)
    db.session.add(candidate)
    db.session.commit()
    return candidate


@pytest.fixture()
def candidate_first_2(user_first):
    """
    Fixture adds candidate for user_first
    """
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20), user_id=user_first.id)
    db.session.add(candidate)
    db.session.commit()
    return candidate


@pytest.fixture()
def candidate_second(user_first):
    """
    Fixture adds candidate for user_first
    """
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20), user_id=user_first.id)
    db.session.add(candidate)
    db.session.commit()
    return candidate


@pytest.fixture()
def user_second_candidate(user_second):
    """
    Fixture adds candidate for user_second
    """
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20), user_id=user_second.id)
    db.session.add(candidate)
    db.session.commit()
    return candidate


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def get_auth_header(access_token):
    """
    This returns auth header dict.
    :param access_token: access token of user
    """
    auth_header = {'Authorization': 'Bearer %s' % access_token}
    auth_header.update(JSON_CONTENT_TYPE_HEADER)
    return auth_header
