"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'

import datetime
import json
import pytest

from widget_service.common.models.candidate import CustomField
from widget_service.common.models.candidate import CandidateSource
from widget_service.common.models.candidate import University
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Country
from widget_service.common.models.misc import Culture
from widget_service.common.models.misc import Major
from widget_service.common.models.misc import Organization
from widget_service.common.models.misc import State
from widget_service.common.models.user import Domain
from widget_service.common.models.user import User
from widget_service.common.models.widget import WidgetPage
from widget_service.widget_app import app
from widget_service.widget_app import db

from widget_service.common.utils.handy_functions import randomword
from widget_service.common.utils.db_utils import get_or_create
from widget_service.widget_app.views.utils import parse_interest_ids_from_form
from widget_service.widget_app.views.utils import parse_city_and_state_ids_from_form

APP = app.test_client()

@pytest.fixture(autouse=True)
def test_org(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(randomword(8)))
    test_org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
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
def create_test_domain(test_culture, test_org, request):
    test_domain = Domain(name=randomword(40), usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(randomword(100)),
                         default_culture_id=test_culture.id,
                         settings_json=randomword(55), updated_time=datetime.datetime.now())

    test_domain2 = Domain(name=randomword(40), usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(randomword(100)),
                         default_culture_id=test_culture.id,
                         settings_json=randomword(55), updated_time=datetime.datetime.now())

    db.session.add(test_domain)
    db.session.add(test_domain2)
    db.session.commit()
    def fin():
        try:
            db.session.delete(test_domain)
            db.session.delete(test_domain2)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_domain


@pytest.fixture(autouse=True)
def create_test_AOIs(create_test_domain, request):
    aois = []
    sub_aois = []
    # Create our parent categories.
    for i in xrange(10):
        aois.append(
            AreaOfInterest(id=i+1, domain_id=create_test_domain.id, description=randomword(16),
                           parent_id=None)
        )
    for i in xrange(2):
            aois.append(
                AreaOfInterest(domain_id=create_test_domain.id + 1, description=randomword(16),
                               parent_id=None)
            )
    db.session.bulk_save_objects(aois)
    # Create our sub-categories.
    parent_id = aois[0].id
    for i in xrange(2):
            sub_aois.append(
                AreaOfInterest(domain_id=create_test_domain.id, description=randomword(16),
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
def create_test_country(request):
    test_country = Country(name='United States', code='U.S.A')
    db.session.add(test_country)
    db.session.commit()
    def fin():
        try:
            db.session.delete(test_country)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_country


@pytest.fixture(autouse=True)
def create_test_state(create_test_country, request):
    test_state = State(name='California', alpha_code='potato', country_id=create_test_country.id,
                       abbreviation='CA')
    db.session.add(test_state)
    db.session.commit()
    def fin():
        try:
            db.session.delete(test_state)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_state


@pytest.fixture(autouse=True)
def create_test_universities(create_test_state, request):
    universities = []
    for i in xrange(5):
        universities.append(
            University(name=randomword(35), state_id=create_test_state.id)
        )
    db.session.bulk_save_objects(universities)
    def fin():
        db.session.query(University).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return universities


@pytest.fixture(autouse=True)
def create_test_user(create_test_domain, request):
    user_attrs = dict(
        domain_id=create_test_domain.id, first_name='Jamtry', last_name='Jonas',
        password='pbkdf2(1000,64,sha512)$bd913bac5e55a39b$ea5a0a2a2d156003faaf7986ea4cba3f25607e43ecffb36e0d2b82381035bbeaded29642a1dd6673e922f162d322862459dd3beedda4501c90f7c14b3669cd72',
        email='jamtry@{}.com'.format(randomword(7)), added_time=datetime.datetime(2050, 4, 26)
    )
    test_user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        db.session.add(test_user)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_user)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_user


@pytest.fixture(autouse=True)
def create_test_candidate_source(create_test_domain, request):
    test_source = CandidateSource(description=randomword(40), notes=randomword(40),
                                  domain_id=create_test_domain.id)
    db.session.add(test_source)
    db.session.commit()
    def fin():
        try:
            db.session.delete(test_source)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_source


@pytest.fixture(autouse=True)
def create_test_majors(create_test_domain, request):
    majors = []
    for i in xrange(5):
        majors.append(Major(name=randomword(18), domain_id=create_test_domain.id))
    db.session.bulk_save_objects(majors)
    def fin():
        db.session.query(Major).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return majors




@pytest.fixture(autouse=True)
def create_test_widget_page(create_test_user, create_test_candidate_source, request):
    test_widget_page = WidgetPage(url=randomword(20), page_views=0, sign_ups=0,
                                  widget_name=randomword(20), user_id=create_test_user.id,
                                  candidate_source_id=create_test_candidate_source.id,
                                  welcome_email_text=randomword(40),
                                  welcome_email_html=randomword(40),
                                  welcome_email_subject=randomword(40),
                                  request_email_text=randomword(40),
                                  request_email_html=randomword(40),
                                  request_email_subject=randomword(40),
                                  email_source=randomword(40), reply_address=randomword(40),
                                  widget_html=randomword(200), s3_location=randomword(12)
                                  )
    db.session.add(test_widget_page)
    db.session.commit()
    def fin():
        try:
            db.session.delete(test_widget_page)
            db.session.commit()
        except Exception as e:
            print "Received exception deleting widget_page %s: %s" % (test_widget_page, e)
            pass
    request.addfinalizer(fin)
    return test_widget_page


@pytest.fixture(autouse=True)
def create_test_extra_fields_location(create_test_domain, request):
    state_field = CustomField(domain_id=create_test_domain.id, name='State of Interest',
                              type='string', added_time=datetime.datetime.now(),
                              updated_time=datetime.datetime.now())
    db.session.add(state_field)
    db.session.commit()

    city_field = CustomField(domain_id=create_test_domain.id, name='City of Interest',
                              type='string', added_time=datetime.datetime.now(),
                              updated_time=datetime.datetime.now())
    db.session.add(city_field)
    db.session.commit()
    def fin():
        db.session.query(CustomField).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return [state_field, city_field]


def test_api_returns_domain_filtered_aois(create_test_widget_page, request):
    response = APP.get('/v1/interests/{}'.format(create_test_widget_page.widget_name))
    assert response.status_code == 200
    assert len(json.loads(response.data)['primary_interests']) == 10
    assert len(json.loads(response.data)['secondary_interests']) == 2


def test_api_returns_university_name_list(request):
    response = APP.get('/v1/universities')
    assert response.status_code == 200
    assert len(json.loads(response.data)['universities']) == 5


def test_api_returns_majors_name_list(create_test_domain, request):
    response = APP.get('/v1/majors/{}'.format(create_test_domain.name))
    assert response.status_code == 200
    assert len(json.loads(response.data)['majors']) == 5


def test_get_call_returns_widget_page_html(create_test_widget_page, request):
    response = APP.get('/v1/widget/{}'.format(create_test_widget_page.widget_name))
    assert response.status_code == 200
    assert response.data == create_test_widget_page.widget_html


def test_post_call_creates_candidate_object(create_test_widget_page, create_test_AOIs, request):
    subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).first()
    parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
    parent_category_2 = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.id!=parent_category_1.id).filter(
        AreaOfInterest.parent_id==None).first()
    aoi_string = "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
        parent_category_without_sub=parent_category_2.description,
        parent_category_with_sub=parent_category_1.description,
        subcategory=subcategory.description)
    candidate_dict = {
        'firstName': randomword(12),
        'lastName': randomword(12),
        'emailAdd': '{}@gmail.com'.format(randomword(12)),
        'hidden-tags-aoi': aoi_string,
        'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona'
    }
    with APP as c:
        post_response = c.post('/v1/widget/{}'.format(create_test_widget_page.widget_name), data=candidate_dict)
    assert post_response.status_code == 200


def test_parse_interest_ids_from_form(request):
    subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).first()
    parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
    parent_category_2 = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.id!=parent_category_1.id).filter(
        AreaOfInterest.parent_id==None).first()
    test_string = "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
        parent_category_without_sub=parent_category_2.description,
        parent_category_with_sub=parent_category_1.description,
        subcategory=subcategory.description)
    processed_ids = parse_interest_ids_from_form(test_string)
    assert processed_ids == [
        {'id': parent_category_2.id}, {'id': subcategory.id}
    ]


def test_parse_location_ids_from_form(create_test_extra_fields_location, request):
    state_custom_field_id = create_test_extra_fields_location[0].id
    city_custom_field_id = create_test_extra_fields_location[1].id
    test_string = 'Northern California: All Cities|Southern California: Pomona'
    processed_ids = parse_city_and_state_ids_from_form(test_string)
    assert processed_ids == [
        {'id': state_custom_field_id, 'value': 'Northern California'},
        {'id': city_custom_field_id, 'value': 'Pomona'}
    ]
