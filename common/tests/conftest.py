# Standard Library
from datetime import datetime
import random, string, uuid

# Third Party
import pytest
from common.utils.common_functions import get_or_create

# Application Specific
from activity_service.activities_app import app
from activity_service.common.models.db import db
from activity_service.common.models.misc import (Activity, Culture, Organization)
from activity_service.common.models.candidate import Candidate
from activity_service.common.models.user import (Client, Domain, Token, User)

ISO_FORMAT = '%Y-%m-%d %H:%M'
APP = app.test_client()


# todo: authentication expires in 2 hours. For testing, we might need a referesh token unless if all tests run in two hours
@pytest.fixture()
def get_auth_token(sample_user):
    """
    :param test_user:
    :return:
    """
    # client_id and client_secret can be any arbitrary string
    client_id = str(uuid.uuid4())[0:8]
    client_secret = str(uuid.uuid4())[0:8]

    # Add cline_id and client_secret to the database
    new_client = Client(client_id=client_id, client_secret=client_secret)
    db.session.add(new_client)
    db.session.commit()

    user_email = sample_user.email
    user_password = sample_user.password

    return dict(email=user_email, password=user_password, client_id=client_id,
                client_secret=client_secret)


@pytest.fixture(autouse=True)
def sample_user(test_domain):
    user_attrs = dict(
        domain_id=test_domain.id, first_name='Jamtry', last_name='Jonas',

        password='pbkdf2(1000,64,sha512)$a97efdd8d6b0bf7f$55de0d7bafb29a88e7596542aa927ac0e1fbc30e94db2c5215851c72294ebe01fb6461b27f0c01b9bd7d3ce4a180707b6652ba2334c7a2b0fcb93c946aa8b4ec',

        email='sample_user@{}.com'.format(randomword(7)), added_time=datetime(2050, 4, 26)
    )
    user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        print "$$$$$ CREATED $$$$$"
        db.session.add(user)
        db.session.commit()

    return user


def revoke_auth_token():
    pass


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


