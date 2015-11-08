"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'

import datetime
import json
import pytest

from widget_service.common.models.candidate import CandidateSource
from widget_service.common.models.misc import CustomField
from widget_service.common.models.candidate import EmailLabel
from widget_service.common.models.candidate import University
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Country
from widget_service.common.models.misc import Culture
from widget_service.common.models.misc import Major
from widget_service.common.models.misc import Organization
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
def test_org(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(random_word(8)))
    test_org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
    if created:
        db.session.add(test_org)
        db.session.commit()

    def fin():
        db.session.delete(test_org)
        db.session.commit()
    request.addfinalizer(fin)
    return test_org


@pytest.fixture(autouse=True)
def test_culture(request):
    culture_attrs = dict(description='Foo {}'.format(random_word(12)), code=random_word(5))
    test_culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(test_culture)
        db.session.commit()

    def fin():
        db.session.delete(test_culture)
        db.session.commit()
    request.addfinalizer(fin)
    return test_culture


@pytest.fixture(autouse=True)
def test_domain(test_culture, test_org, request):
    test_domain = Domain(name=random_word(40),
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime.today(),
                         organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(random_word(100)),
                         default_culture_id=test_culture.id,
                         settings_json=random_word(55), updated_time=datetime.datetime.now())
    db.session.add(test_domain)
    db.session.commit()

    def fin():
        db.session.delete(test_domain)
        db.session.commit()
    request.addfinalizer(fin)
    return test_domain


@pytest.fixture(autouse=True)
def second_domain(test_culture, test_org, request):
    test_domain2 = Domain(name=random_word(40),
                          expiration=datetime.datetime(2050, 4, 26),
                          added_time=datetime.datetime.today(),
                          organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                          default_tracking_code=1, default_from_name=(random_word(100)),
                          default_culture_id=test_culture.id,
                          settings_json=random_word(55), updated_time=datetime.datetime.now())
    db.session.add(test_domain2)
    db.session.commit()

    def fin():
        db.session.delete(test_domain2)
        db.session.commit()
    request.addfinalizer(fin)
    return test_domain2


@pytest.fixture(autouse=True)
def areas_of_interest(test_domain, second_domain, request):
    aois = []
    sub_aois = []
    # Create our parent categories.
    for i in xrange(10):
        aois.append(
            AreaOfInterest(domain_id=test_domain.id, description=random_word(16),
                           parent_id=None)
        )
    for i in xrange(2):
            aois.append(
                AreaOfInterest(domain_id=second_domain.id, description=random_word(16),
                               parent_id=None)
            )
    db.session.bulk_save_objects(aois)
    # Create our sub-categories.
    parent_id = db.session.query(AreaOfInterest).filter_by(domain_id=test_domain.id).first().id
    for i in xrange(2):
            sub_aois.append(
                AreaOfInterest(domain_id=test_domain.id, description=random_word(16),
                               parent_id=parent_id)
            )
    db.session.bulk_save_objects(sub_aois)

    def fin():
        db.session.query(AreaOfInterest).delete()
        db.session.commit()
    request.addfinalizer(fin)
    aois.extend(sub_aois)
    return aois


@pytest.fixture(autouse=True)
def test_country(request):
    test_country = Country(name='United States', code='U.S.A')
    db.session.add(test_country)
    db.session.commit()

    def fin():
        db.session.delete(test_country)
        db.session.commit()
    request.addfinalizer(fin)
    return test_country


@pytest.fixture(autouse=True)
def test_universities(request):
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
def test_user(test_domain, request):
    user_attrs = dict(
        domain_id=test_domain.id, first_name='Jamtry', last_name='Jonas',
        password='password', email='jamtry@{}.com'.format(random_word(7)),
        added_time=datetime.datetime.today()
    )
    test_user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        db.session.add(test_user)
        db.session.commit()

    def fin():
        db.session.delete(test_user)
        db.session.commit()
    request.addfinalizer(fin)
    return test_user


@pytest.fixture(autouse=True)
def test_candidate_source(test_domain, request):
    test_source = CandidateSource(description=random_word(40), notes=random_word(40),
                                  domain_id=test_domain.id)
    db.session.add(test_source)
    db.session.commit()

    def fin():
        db.session.delete(test_source)
        db.session.commit()
    request.addfinalizer(fin)
    return test_source


@pytest.fixture(autouse=True)
def test_majors(test_domain, request):
    majors = []
    for i in xrange(5):
        majors.append(Major(name=random_word(18), domain_id=test_domain.id))
    db.session.bulk_save_objects(majors)

    def fin():
        db.session.query(Major).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return majors


@pytest.fixture(autouse=True)
def test_widget_page(test_user, test_candidate_source, request):
    test_widget_page = WidgetPage(url=random_word(20), page_views=0, sign_ups=0,
                                  widget_name=random_word(20), user_id=test_user.id,
                                  candidate_source_id=test_candidate_source.id,
                                  welcome_email_text=random_word(40),
                                  welcome_email_html=random_word(40),
                                  welcome_email_subject=random_word(40),
                                  request_email_text=random_word(40),
                                  request_email_html=random_word(40),
                                  request_email_subject=random_word(40),
                                  email_source=random_word(40), reply_address=random_word(40),
                                  unique_key=random_word(12)
                                  )
    db.session.add(test_widget_page)
    db.session.commit()

    def fin():
        db.session.delete(test_widget_page)
        db.session.commit()
    request.addfinalizer(fin)
    return test_widget_page


@pytest.fixture(autouse=True)
def test_extra_fields_location(test_domain, request):
    state_field = CustomField(domain_id=test_domain.id, name='State of Interest',
                              type='string', added_time=datetime.datetime.now(),
                              updated_time=datetime.datetime.now())
    db.session.add(state_field)
    db.session.commit()

    city_field = CustomField(domain_id=test_domain.id, name='City of Interest',
                             type='string', added_time=datetime.datetime.now(),
                             updated_time=datetime.datetime.now())
    db.session.add(city_field)
    db.session.commit()

    nuid_field = CustomField(domain_id=test_domain.id, name='NUID', type='string',
                             added_time=datetime.datetime.now(),
                             updated_time=datetime.datetime.now())
    db.session.add(nuid_field)
    db.session.commit()

    subscription_pref_field = CustomField(domain_id=test_domain.id, name='Subscription Preference',
                                          type='string', added_time=datetime.datetime.now(),
                                          updated_time=datetime.datetime.now())
    db.session.add(subscription_pref_field)
    db.session.commit()

    def fin():
        db.session.query(CustomField).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return [state_field, city_field, subscription_pref_field]


@pytest.fixture(autouse=True)
def test_oauth_credentials(request):
    test_client = Client(client_id=random_word(16), client_secret=random_word(18))
    db.session.add(test_client)
    db.session.commit()
    app.config['WIDGET_CLIENT_ID'] = test_client.client_id
    app.config['WIDGET_CLIENT_SECRET'] = test_client.client_secret

    def fin():
        db.session.query(Token).delete()
        db.session.commit()
        db.session.query(Client).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return {'test_client': test_client}


@pytest.fixture()
def test_expired_oauth_credentials(test_user, request):
    test_client = Client(client_id=random_word(16), client_secret=random_word(18))
    db.session.add(test_client)
    db.session.commit()
    app.config['WIDGET_CLIENT_ID'] = test_client.client_id
    app.config['WIDGET_CLIENT_SECRET'] = test_client.client_secret
    test_token = Token(client_id=test_client.client_id, user_id=test_user.id, token_type='bearer',
                       access_token=random_word(18), refresh_token=random_word(18),
                       expires=datetime.datetime.now() - datetime.timedelta(days=30))
    db.session.add(test_token)
    db.session.commit()

    def fin():
        db.session.query(Token).delete()
        db.session.commit()
        db.session.query(Client).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return {'test_client': test_client}


@pytest.fixture(autouse=True)
def test_email_label(request):
    email_label_args = {'id': 1, 'description': 'Primary'}
    test_email_label, created = get_or_create(db.session, EmailLabel, **email_label_args)
    if not created:
        db.session.commit()
    return test_email_label


def test_api_returns_domain_filtered_aois(test_domain, request):
    response = APP.get('/v1/domains/{}/interests'.format(gt_url_encrypt(test_domain.id)))
    assert response.status_code == 200
    assert len(json.loads(response.data)['primary_interests']) == 10
    assert len(json.loads(response.data)['secondary_interests']) == 2


def test_api_returns_university_name_list(request):
    response = APP.get('/v1/universities')
    assert response.status_code == 200
    assert len(json.loads(response.data)['universities_list']) == 5


def test_api_returns_majors_name_list(test_domain, request):
    response = APP.get('/v1/domains/{}/majors'.format(gt_url_encrypt(test_domain.id)))
    assert response.status_code == 200
    assert len(json.loads(response.data)['majors']) == 5


def test_military_candidate(test_widget_page, request):
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
            gt_url_encrypt(test_widget_page.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_university_candidate(test_widget_page, request):
    aoi_string = gen_mock_aois()
    candidate_dict = {
        'name': random_word(12),
        'emailAdd': '{}@gmail.com'.format(random_word(12)),
        'city': random_word(10),
        'state': random_word(10),
        'university': random_word(10),
        'degree': random_word(10),
        'major': random_word(10),
        'graduation': random_word(8),
        'hidden-tags-aoi': aoi_string,
        'nuid': random_word(8),
        'jobFrequency': 'Monthly'
    }
    with APP as c:
        post_response = c.post('/v1/domains/potato/widgets/{}'.format(
            gt_url_encrypt(test_widget_page.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_corporate_candidate(test_widget_page, request):
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
            gt_url_encrypt(test_widget_page.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.data


def test_expired_token_refreshes(test_widget_page, test_expired_oauth_credentials, request):
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
            gt_url_encrypt(test_widget_page.id)), data=candidate_dict)
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


def test_parse_location_ids_from_form(test_extra_fields_location, request):
    state_custom_field_id = test_extra_fields_location[0].id
    city_custom_field_id = test_extra_fields_location[1].id
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
