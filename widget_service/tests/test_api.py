"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'
# Standard Library.
import datetime
import json
# Third Party/Module specific.
import requests as r
from .fixtures import areas_of_interest
from .fixtures import candidate_source_fixture
from .fixtures import candidate_status_fixture
from .fixtures import country_fixture
from .fixtures import culture_fixture
from .fixtures import domain_fixture
from .fixtures import email_label_fixture
from .fixtures import expired_oauth_credentials
from .fixtures import extra_field_fixtures
from .fixtures import major_fixtures
from .fixtures import org_fixture
from .fixtures import product_fixture
from .fixtures import second_domain
from .fixtures import university_fixtures
from .fixtures import user_fixture
from .fixtures import valid_oauth_credentials
from .fixtures import widget_page_fixture
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.utils.handy_functions import random_word
from widget_service.widget_app.flask_scripts.url_encode import gt_url_encrypt
from widget_service.widget_app.views.utils import parse_city_and_state_ids_from_form
from widget_service.widget_app.views.utils import parse_interest_ids_from_form
from widget_service.common.models.db import db
from widget_service.widget_app import app


db.init_app(app)
db.app = app
APP_URL = 'http://0.0.0.0:8006/v1'


def test_api_returns_domain_filtered_aois(domain_fixture, request):
    response = r.get('{}/domains/{}/interests'.format(APP_URL, gt_url_encrypt(domain_fixture.id)))
    assert response.status_code == 200
    assert len(json.loads(response.content)['primary_interests']) == 10
    assert len(json.loads(response.content)['secondary_interests']) == 2


def test_api_returns_university_name_list(request):
    response = r.get('{}/universities'.format(APP_URL))
    assert response.status_code == 200
    assert len(json.loads(response.content)['universities_list']) == 5


def test_api_returns_majors_name_list(domain_fixture, request):
    response = r.get('{}/domains/{}/majors'.format(APP_URL, gt_url_encrypt(domain_fixture.id)))
    assert response.status_code == 200
    assert len(json.loads(response.content)['majors']) == 5


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

    post_response = r.post('{}/domains/potato/widgets/{}'.format(
        APP_URL, gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.content


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

    post_response = r.post('{}/domains/potato/widgets/{}'.format(
        APP_URL, gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.content


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

    post_response = r.post('{}/domains/potato/widgets/{}'.format(
        APP_URL, gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.content


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

    post_response = r.post('{}/domains/potato/widgets/{}'.format(
        APP_URL, gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
    assert post_response.status_code == 201
    # TODO expand to check DB that our fields are there
    assert 'success' in post_response.content


def test_parse_interest_ids_from_form(request):
    subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).first()
    parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
    parent_category_2 = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.id!=parent_category_1.id).filter(
        AreaOfInterest.parent_id == None).first()
    test_string = "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
        parent_category_without_sub=parent_category_2.name,
        parent_category_with_sub=parent_category_1.name,
        subcategory=subcategory.name)
    processed_ids = parse_interest_ids_from_form(test_string)
    assert processed_ids == [
        {'area_of_interest_id': parent_category_2.id}, {'area_of_interest_id': subcategory.id}
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


def test_health_check():
    import requests
    response = requests.get('http://127.0.0.1:8006/healthcheck')
    assert response.status_code == 200


def gen_mock_aois():
    subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id != None).first()
    parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
    parent_category_2 = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.id!=parent_category_1.id).filter(
        AreaOfInterest.parent_id == None).first()
    return "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
        parent_category_without_sub=parent_category_2.name,
        parent_category_with_sub=parent_category_1.name,
        subcategory=subcategory.name)
