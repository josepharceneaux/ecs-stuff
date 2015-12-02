__author__ = 'Erik Farmer'
# Standard Library
from datetime import datetime
from datetime import timedelta
import json
# Third Party/Framework Specific
from _mysql_exceptions import IntegrityError
import pytest
# Application Specific
from activity_service.activities_app import db
from activity_service.common.models.candidate import Candidate
from activity_service.common.models.candidate import CandidateSource
from activity_service.common.models.misc import Activity
from activity_service.common.models.misc import Culture
from activity_service.common.models.misc import Organization
from activity_service.common.models.user import Client
from activity_service.common.models.user import Domain
from activity_service.common.models.user import Token
from activity_service.common.models.user import User
from activity_service.common.utils.db_utils import get_or_create
from activity_service.common.utils.db_utils import require_integrity
from activity_service.common.utils.handy_functions import random_word


@pytest.fixture(autouse=True)
def activities_fixture(user_fixture, candidate_source_fixture, request):
    activities = []
    today = datetime.today()
    first_name, last_name = user_fixture.first_name, user_fixture.last_name
    activities.append(Activity(added_time=today + timedelta(hours=-2), source_table='user',
                               source_id=1, type=12, user_id=user_fixture.id,
                               params=json.dumps({'lastName': last_name, 'firstName': first_name})))
    for i in xrange(3):
        activities.append(
            Activity(added_time=today, source_table='user', source_id=1,
                     type=12, user_id=user_fixture.id, params=json.dumps({'lastName': last_name,
                                                                          'firstName': first_name}))
        )
    db.session.bulk_save_objects(activities)

    @require_integrity(database_object=db)
    def fin():
        db.session.query(Activity).filter(Activity.user_id == user_fixture.id).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return activities


@pytest.fixture(autouse=True)
def candidate_fixture(user_fixture, culture_fixture, candidate_source_fixture, request):
    candidate_attrs = dict(
        first_name=random_word(4), last_name=random_word(6), formatted_name=random_word(10),
        is_web_hidden=0, is_mobile_hidden=0, added_time=datetime.today(), user_id=user_fixture.id,
        domain_can_read=1, domain_can_write=1, source_id=candidate_source_fixture.id,
        source_product_id=2, objective=random_word(6), culture_id=culture_fixture.id, is_dirty=0
    )
    candidate, created = get_or_create(db.session, Candidate, defaults=None, **candidate_attrs)
    if created:
        db.session.add(candidate)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(candidate)
        db.session.commit()

    request.addfinalizer(fin)
    return candidate


@pytest.fixture(autouse=True)
def candidate_source_fixture(domain_fixture, request):
    source = CandidateSource(description=random_word(40), notes=random_word(40),
                             domain_id=domain_fixture.id)
    db.session.add(source)
    db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(source)
        db.session.commit()
    request.addfinalizer(fin)
    return source


@pytest.fixture(autouse=True)
def client_fixture(request):
    client_attrs = dict(client_id=random_word(30), client_secret=random_word(12))
    client, created = get_or_create(db.session, Client, defaults=None, **client_attrs)
    if created:
        db.session.add(client)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(client)
        db.session.commit()
    request.addfinalizer(fin)
    return client


@pytest.fixture(autouse=True)
def culture_fixture(request):
    culture_attrs = dict(description=random_word(12), code=random_word(5))
    culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(culture)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(culture)
        db.session.commit()
    request.addfinalizer(fin)
    return culture


@pytest.fixture(autouse=True)
def domain_fixture(org_fixture, culture_fixture, request):
    domain_attrs = dict(
        name=random_word(10).format(), usage_limitation=-1, added_time=datetime.today(),
        organization_id=org_fixture.id, is_fair_check_on=0, is_active=1,
        default_culture_id=culture_fixture.id, expiration=datetime(2050, 4, 26)
    )
    domain, created = get_or_create(db.session, Domain, defaults=None, **domain_attrs)
    if created:
        db.session.add(domain)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(domain)
        db.session.commit()
    request.addfinalizer(fin)
    return domain


@pytest.fixture(autouse=True)
def org_fixture(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(random_word(8)))
    org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
    if created:
        db.session.add(org)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(org)
        db.session.commit()
    request.addfinalizer(fin)
    return org


@pytest.fixture(autouse=True)
def token_fixture(client_fixture, user_fixture, request):
    token_attrs = dict(client_id=client_fixture.client_id, user_id=user_fixture.id,
                       token_type='bearer', access_token=random_word(26),
                       refresh_token=random_word(26), expires=datetime(2050, 4, 26))
    token, created = get_or_create(db.session, Token, defaults=None, **token_attrs)
    if created:
        db.session.add(token)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(token)
        db.session.commit()
    request.addfinalizer(fin)
    return token


@pytest.fixture(autouse=True)
def user_fixture(domain_fixture, request):
    user_attrs = dict(
        domain_id=domain_fixture.id, first_name='Jamtry', last_name='Jonas',
        password=random_word(12), email=random_word(7), added_time=datetime(2050, 4, 26)
    )
    user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        db.session.add(user)
        db.session.commit()

    @require_integrity(database_object=db)
    def fin():
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(fin)
    return user
