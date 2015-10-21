# Standard Library
from datetime import datetime
import random, string, uuid

# Third Party
import pytest, requests
from common.utils.common_functions import get_or_create

# Application Specific
# TODO:
from activity_service.activities_app import app
from activity_service.common.models.db import db
from activity_service.common.models.misc import (Culture, Organization)
from activity_service.common.models.user import (Client, Domain, User, Token)

ISO_FORMAT = '%Y-%m-%d %H:%M'
APP = app.test_client()
USER_HASHED_PASSWORD = 'pbkdf2(1000,64,sha512)$a97efdd8d6b0bf7f$55de0d7bafb29a88e7596542aa927ac0e1fbc30e94db2c5215851c72294ebe01fb6461b27f0c01b9bd7d3ce4a180707b6652ba2334c7a2b0fcb93c946aa8b4ec'


class UserAuthentication():
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
    resp = requests.post('http://localhost:8001/oauth2/token', data=data)
    assert resp.status_code == 200
    return resp.json()


def revoke_token(user_logout_credentials):
    access_token = user_logout_credentials['token'].access_token
    revoke_data = {'client_id': user_logout_credentials['client_id'],
                   'client_secret': user_logout_credentials['client_secret'],
                   'token': access_token,
                   'grant_type': 'password'}
    resp = requests.post('http://localhost:8001/oauth2/revoke', data=revoke_data)
    assert resp.status_code == 200
    return


@pytest.fixture(autouse=True)
def sample_user(request, test_domain):
    user_attrs = dict(
        domain_id=test_domain.id, first_name='Jamtry', last_name='Jonas',
        password=USER_HASHED_PASSWORD,
        email='sample_user@{}.com'.format(randomword(7)), added_time=datetime(2050, 4, 26)
    )
    user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        db.session.add(user)
        db.session.commit()

    def fin():
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return user


@pytest.fixture(autouse=True)
def test_domain(test_org, test_culture, request):
    domain_attrs = dict(
        name=randomword(10).format(), usage_limitation=-1, added_time=datetime.today(),
        organization_id=test_org.id, is_fair_check_on=0, is_active=1,
        default_culture_id=test_culture.id, expiration=datetime(2050, 4, 26)
    )
    test_domain, created = get_or_create(db.session, Domain, defaults=None, **domain_attrs)
    if created:
        db.session.add(test_domain)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_domain)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_domain


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
            pass

    request.addfinalizer(fin)
    return test_org


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


