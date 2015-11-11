"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'

import datetime
import json
import pytest

from widget_service.common.models.candidate import CandidateSource
from widget_service.common.models.candidate import CandidateStatus
from widget_service.common.models.candidate import CandidateCustomField
from widget_service.common.models.associations import CandidateAreaOfInterest
from widget_service.common.models.misc import CustomField
from widget_service.common.models.email import EmailLabel
from widget_service.common.models.university import University
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Country
from widget_service.common.models.misc import Culture
from widget_service.common.models.misc import Major
from widget_service.common.models.misc import Organization
from widget_service.common.models.misc import Product
from widget_service.common.models.user import Client
from widget_service.common.models.user import Domain
from widget_service.common.models.user import Token
from widget_service.common.models.user import User
from widget_service.common.models.widget import WidgetPage
from widget_service.widget_app.flask_scripts.url_encode import gt_url_encrypt
from widget_service.widget_app import app
from widget_service.widget_app import db

from widget_service.common.utils.handy_functions import random_word
from widget_service.common.utils.db_utils import get_or_create
from widget_service.widget_app.views.utils import parse_interest_ids_from_form
from widget_service.widget_app.views.utils import parse_city_and_state_ids_from_form

APP = app.test_client()


@pytest.fixture(autouse=True)
def org_fixture(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(random_word(8)))
    org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
    if created:
        db.session.add(org)
        db.session.commit()

    def fin():
        db.session.delete(org)
        db.session.commit()
    request.addfinalizer(fin)
    return org


@pytest.fixture(autouse=True)
def culture_fixture(request):
    culture_attrs = dict(description='Foo {}'.format(random_word(12)), code=random_word(5))
    culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(culture)
        db.session.commit()

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

    def fin():
        db.session.query(CandidateCustomField).delete()
        db.session.commit()
        db.session.query(CustomField).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return [state_field, city_field, subscription_pref_field]


@pytest.fixture(autouse=True)
def valid_oauth_credentials(request):
    client = Client(client_id=random_word(16), client_secret=random_word(18))
    db.session.add(client)
    db.session.commit()
    app.config['WIDGET_CLIENT_ID'] = client.client_id
    app.config['WIDGET_CLIENT_SECRET'] = client.client_secret

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
    app.config['WIDGET_CLIENT_ID'] = client.client_id
    app.config['WIDGET_CLIENT_SECRET'] = client.client_secret
    token = Token(client_id=client.client_id, user_id=user_fixture.id, token_type='bearer',
                       access_token=random_word(18), refresh_token=random_word(18),
                       expires=datetime.datetime.now() - datetime.timedelta(days=30))
    db.session.add(token)
    db.session.commit()

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




def test_api_returns_domain_filtered_aois(domain_fixture, request):
    response = APP.get('/v1/domains/{}/interests'.format(gt_url_encrypt(domain_fixture.id)))
    assert response.status_code == 200
    assert len(json.loads(response.data)['primary_interests']) == 10
    assert len(json.loads(response.data)['secondary_interests']) == 2


def test_api_returns_university_name_list(request):
    response = APP.get('/v1/universities')
    assert response.status_code == 200
    assert len(json.loads(response.data)['universities_list']) == 5


def test_api_returns_majors_name_list(domain_fixture, request):
    response = APP.get('/v1/domains/{}/majors'.format(gt_url_encrypt(domain_fixture.id)))
    assert response.status_code == 200
    assert len(json.loads(response.data)['majors']) == 5


def test_military_candidate(widget_page_fixture, request):
    aoi_string = gen_mock_aois()
    candidate_dict = {
        'firstName': random_word(12),
        'lastName': random_word(12),
        'emailAdd': '{}@gmail.com'.format(random_word(12)),
        'hidden-tags-aoi': aoi_string,
        'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona',
        'militaryBranch': 'Air Force',
        'militaryStatus': 'active',
        'militaryGrade': 'E-1',
        'militaryToDate': datetime.datetime.today().isoformat()[:10],
        'jobFrequency': 'Weekly'
    }
    with APP as c:
        post_response = c.post('/v1/domains/potato/widgets/{}'.format(
            gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_university_candidate(widget_page_fixture, request):
    aoi_string = gen_mock_aois()
    candidate_dict = {
        'name': random_word(12),
        'emailAdd': '{}@gmail.com'.format(random_word(12)),
        'city': random_word(10),
        'state': random_word(10),
        'university': random_word(10),
        'degree': random_word(10),
        'major': random_word(10),
        'graduation': '{} {}'.format(random_word(8), 2016),
        'hidden-tags-aoi': aoi_string,
        'nuid': random_word(8),
        'jobFrequency': 'Monthly'
    }
    with APP as c:
        post_response = c.post('/v1/domains/potato/widgets/{}'.format(
            gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_corporate_candidate(widget_page_fixture, request):
    aoi_string = gen_mock_aois()
    candidate_dict = {
        'firstName': random_word(12),
        'lastName': random_word(12),
        'emailAdd': '{}@gmail.com'.format(random_word(12)),
        'hidden-tags-aoi': aoi_string,
        'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona',
        'jobFrequency': 'Daily'
    }
    with APP as c:
        post_response = c.post('/v1/domains/potato/widgets/{}'.format(
            gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_expired_token_refreshes(widget_page_fixture, expired_oauth_credentials, request):
    aoi_string = gen_mock_aois()
    candidate_dict = {
        'firstName': random_word(12),
        'lastName': random_word(12),
        'emailAdd': '{}@gmail.com'.format(random_word(12)),
        'hidden-tags-aoi': aoi_string,
        'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona',
        'jobFrequency': 'Daily'
    }
    with APP as c:
        post_response = c.post('/v1/domains/potato/widgets/{}'.format(
            gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_parse_interest_ids_from_form(request):
    subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).first()
    parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
    parent_category_2 = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.id!=parent_category_1.id).filter(
        AreaOfInterest.parent_id == None).first()
    test_string = "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
        parent_category_without_sub=parent_category_2.description,
        parent_category_with_sub=parent_category_1.description,
        subcategory=subcategory.description)
    processed_ids = parse_interest_ids_from_form(test_string)
    assert processed_ids == [
        {'id': parent_category_2.id}, {'id': subcategory.id}
    ]


def test_parse_location_ids_from_form(extra_field_fixtures, request):
    state_custom_field_id = extra_field_fixtures[0].id
    city_custom_field_id = extra_field_fixtures[1].id
    test_string = 'Northern California: All Cities|Southern California: Pomona'
    processed_ids = parse_city_and_state_ids_from_form(test_string)
    assert processed_ids == [
        {'id': state_custom_field_id, 'value': 'Northern California'},
        {'id': city_custom_field_id, 'value': 'Pomona'}
    ]


def gen_mock_aois():
    subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id != None).first()
    parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
    parent_category_2 = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.id!=parent_category_1.id).filter(
        AreaOfInterest.parent_id == None).first()
    return "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
        parent_category_without_sub=parent_category_2.description,
        parent_category_with_sub=parent_category_1.description,
        subcategory=subcategory.description)
