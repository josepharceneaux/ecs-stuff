"""Test fixtures for Flask Widget MicroService."""
__author__ = 'erik@getTalent.com'
# Standard Library
import datetime
# Third Party/Module specific.
from _mysql_exceptions import IntegrityError
import pytest
from widget_service.common.models.associations import CandidateAreaOfInterest
from widget_service.common.models.candidate import CandidateCustomField
from widget_service.common.models.candidate import CandidateSource
from widget_service.common.models.candidate import CandidateStatus
from widget_service.common.models.db import db
from widget_service.common.models.email import EmailLabel
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Country
from widget_service.common.models.misc import Culture
from widget_service.common.models.misc import CustomField
from widget_service.common.models.misc import Major
from widget_service.common.models.misc import Organization
from widget_service.common.models.misc import Product
from widget_service.common.models.university import University
from widget_service.common.models.user import Client
from widget_service.common.models.user import Domain
from widget_service.common.models.user import Token
from widget_service.common.models.user import User
from widget_service.common.models.widget import WidgetPage
from widget_service.common.utils.db_utils import get_or_create
from widget_service.common.utils.handy_functions import random_word
from widget_service.widget_app import app

db.init_app(app)
db.app = app


def requireIntegrity(func):
  def wrapped(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except IntegrityError:
      db.session.rollback()
  return wrapped

@pytest.fixture(autouse=True)
def org_fixture(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(random_word(8)))
    org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
    if created:
        db.session.add(org)
        db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(org)
        db.session.commit()
    request.addfinalizer(fin)
    return org


@pytest.fixture(autouse=True)
def culture_fixture(request):
    culture_attrs = dict(id=1)
    culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(culture)
        db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(culture)
        db.session.commit()
    request.addfinalizer(fin)
    return culture


@pytest.fixture(autouse=True)
def domain_fixture(culture_fixture, org_fixture, request):
    domain = Domain(name=random_word(40),
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime.today(),
                         organization_id=org_fixture.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(random_word(100)),
                         default_culture_id=culture_fixture.id,
                         settings_json=random_word(55))
    db.session.add(domain)
    db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(domain)
        db.session.commit()
    request.addfinalizer(fin)
    return domain


@pytest.fixture(autouse=True)
def second_domain(culture_fixture, org_fixture, request):
    domain2 = Domain(name=random_word(40),
                          expiration=datetime.datetime(2050, 4, 26),
                          added_time=datetime.datetime.today(),
                          organization_id=org_fixture.id, is_fair_check_on=False, is_active=1,
                          default_tracking_code=1, default_from_name=(random_word(100)),
                          default_culture_id=culture_fixture.id,
                          settings_json=random_word(55))
    db.session.add(domain2)
    db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(domain2)
        db.session.commit()
    request.addfinalizer(fin)
    return domain2


@pytest.fixture(autouse=True)
def areas_of_interest(domain_fixture, second_domain, request):
    aois = []
    sub_aois = []
    # Create our parent categories.
    for i in xrange(10):
        aois.append(
            AreaOfInterest(domain_id=domain_fixture.id, description=random_word(16),
                           parent_id=None)
        )
    for i in xrange(2):
            aois.append(
                AreaOfInterest(domain_id=second_domain.id, description=random_word(16),
                               parent_id=None)
            )
    db.session.bulk_save_objects(aois)
    # Create our sub-categories.
    parent_id = db.session.query(AreaOfInterest).filter_by(domain_id=domain_fixture.id).first().id
    for i in xrange(2):
            sub_aois.append(
                AreaOfInterest(domain_id=domain_fixture.id, description=random_word(16),
                               parent_id=parent_id)
            )
    db.session.bulk_save_objects(sub_aois)
    @requireIntegrity
    def fin():
        db.session.query(CandidateAreaOfInterest).delete()
        db.session.commit()
        db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).delete()
        db.session.commit()
        db.session.query(AreaOfInterest).delete()
        db.session.commit()
    request.addfinalizer(fin)
    aois.extend(sub_aois)
    return aois


@pytest.fixture(autouse=True)
def country_fixture(request):
    country_attrs = dict(id = 1, name = 'United States', code = 'US')
    country, created = get_or_create(db.session, Country, defaults=None, **country_attrs)
    if created:
        db.session.add(country)
        db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(country)
        db.session.commit()
    request.addfinalizer(fin)
    return country


@pytest.fixture(autouse=True)
def university_fixtures(request):
    universities = []
    for i in xrange(5):
        universities.append(
            University(name=random_word(35))
        )
    db.session.bulk_save_objects(universities)
    @requireIntegrity
    def fin():
        db.session.query(University).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return universities


@pytest.fixture(autouse=True)
def user_fixture(domain_fixture, request):
    user_attrs = dict(
        domain_id=domain_fixture.id, first_name='Jamtry', last_name='Jonas',
        password='password', email='jamtry@{}.com'.format(random_word(7)),
        added_time=datetime.datetime.today()
    )
    user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        db.session.add(user)
        db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(user)
        db.session.commit()
    request.addfinalizer(fin)
    return user


@pytest.fixture(autouse=True)
def candidate_source_fixture(domain_fixture, request):
    test_source = CandidateSource(description=random_word(40), notes=random_word(40),
                                  domain_id=domain_fixture.id)
    db.session.add(test_source)
    db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(test_source)
        db.session.commit()
    request.addfinalizer(fin)
    return test_source


@pytest.fixture(autouse=True)
def major_fixtures(domain_fixture, request):
    majors = []
    for i in xrange(5):
        majors.append(Major(name=random_word(18), domain_id=domain_fixture.id))
    db.session.bulk_save_objects(majors)
    @requireIntegrity
    def fin():
        db.session.query(Major).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return majors


@pytest.fixture(autouse=True)
def widget_page_fixture(user_fixture, candidate_source_fixture, request):
    widget_page = WidgetPage(url=random_word(20), page_views=0, sign_ups=0,
                             widget_name=random_word(20), user_id=user_fixture.id,
                             candidate_source_id=candidate_source_fixture.id,
                             welcome_email_text=random_word(40),
                             welcome_email_html=random_word(40),
                             welcome_email_subject=random_word(40),
                             request_email_text=random_word(40),
                             request_email_html=random_word(40),
                             request_email_subject=random_word(40),
                             email_source=random_word(40), reply_address=random_word(40),
                             unique_key=random_word(12)
                             )
    db.session.add(widget_page)
    db.session.commit()
    @requireIntegrity
    def fin():
        db.session.delete(widget_page)
        db.session.commit()
    request.addfinalizer(fin)
    return widget_page


@pytest.fixture(autouse=True)
def extra_field_fixtures(domain_fixture, request):
    state_field = CustomField(domain_id=domain_fixture.id, name='State of Interest',
                              type='string', added_time=datetime.datetime.now(),
                              updated_time=datetime.datetime.now())
    db.session.add(state_field)
    db.session.commit()

    city_field = CustomField(domain_id=domain_fixture.id, name='City of Interest',
                             type='string', added_time=datetime.datetime.now(),
                             updated_time=datetime.datetime.now())
    db.session.add(city_field)
    db.session.commit()

    nuid_field = CustomField(domain_id=domain_fixture.id, name='NUID', type='string',
                             added_time=datetime.datetime.now(),
                             updated_time=datetime.datetime.now())
    db.session.add(nuid_field)
    db.session.commit()

    subscription_pref_field = CustomField(domain_id=domain_fixture.id, name='Subscription Preference',
                                          type='string', added_time=datetime.datetime.now(),
                                          updated_time=datetime.datetime.now())
    db.session.add(subscription_pref_field)
    db.session.commit()
    @requireIntegrity
    def fin():
        db.session.query(CandidateCustomField).delete()
        db.session.commit()
        db.session.query(CustomField).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return [state_field, city_field, subscription_pref_field]


@pytest.fixture(autouse=True)
def valid_oauth_credentials(request):
    client_attrs = dict(client_id='dev_client_id', client_secret='dev_client_secret')
    client, created = get_or_create(db.session, Client, defaults=None, **client_attrs)
    if created:
        db.session.add(client)
        db.session.commit()
    @requireIntegrity
    def fin():
        db.session.query(Token).delete()
        db.session.commit()
        db.session.query(Client).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return client


@pytest.fixture()
def expired_oauth_credentials(user_fixture, request):
    client = Client(client_id=random_word(16), client_secret=random_word(18))
    db.session.add(client)
    db.session.commit()
    token = Token(client_id=client.client_id, user_id=user_fixture.id, token_type='bearer',
                       access_token=random_word(18), refresh_token=random_word(18),
                       expires=datetime.datetime.now() - datetime.timedelta(days=30))
    db.session.add(token)
    db.session.commit()
    @requireIntegrity
    def fin():
        db.session.query(Token).delete()
        db.session.commit()
        db.session.query(Client).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return client


@pytest.fixture(autouse=True)
def email_label_fixture(request):
    email_label_args = {'id': 1, 'description': 'Primary'}
    email_label, created = get_or_create(db.session, EmailLabel, **email_label_args)
    if not created:
        db.session.commit()
    return email_label


@pytest.fixture(autouse=True)
def candidate_status_fixture(request):
    status_attrs = dict(id=1)
    status, created = get_or_create(db.session, CandidateStatus, defaults=None, **status_attrs)
    if created:
        db.session.add(status)
        db.session.commit()
    return status


@pytest.fixture(autouse=True)
def product_fixture(request):
    product_attrs = {'id': 2}
    product, created = get_or_create(db.session, Product, defaults=None, **product_attrs)
    if created:
        db.session.add(product)
        db.session.commit()
    return product
