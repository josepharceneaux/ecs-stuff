"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'
# Standard Library.
import datetime
# Third Party/Module specific.
import requests as r
from widget_service.common.tests.conftest import domain_aois
from widget_service.common.tests.conftest import domain_custom_field_categories
from widget_service.common.tests.conftest import domain_custom_fields
from widget_service.common.tests.conftest import domain_first
from widget_service.common.tests.conftest import first_group
from widget_service.common.tests.conftest import talent_pool
from widget_service.common.tests.conftest import user_first
from widget_service.common.tests.conftest import widget_page

# from widget_service.app.views.utils import parse_city_and_state_ids_from_form
# from widget_service.app.views.utils import parse_interest_ids_from_form
from widget_service.common.models.db import db
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.routes import WidgetApiUrl
from widget_service.common.utils.handy_functions import random_word

# db.init_app(app)
# db.app = app
#
#
# def test_api_returns_domain_filtered_aois(domain_fixture, request):
#     response = r.get(WidgetApiUrl.DOMAIN_INTERESTS % gt_url_encrypt(domain_fixture.id))
#     assert response.status_code == 200
#     assert len(json.loads(response.content)['primary_interests']) == 10
#     assert len(json.loads(response.content)['secondary_interests']) == 2
#
#
# def test_api_returns_university_name_list(request):
#     response = r.get(WidgetApiUrl.UNIVERSITIES)
#     assert response.status_code == 200
#     assert len(json.loads(response.content)['universities_list']) == 5
#
#
# def test_api_returns_majors_name_list(domain_fixture, request):
#     response = r.get(WidgetApiUrl.DOMAIN_MAJORS % gt_url_encrypt(domain_fixture.id))
#     assert response.status_code == 200
#     assert len(json.loads(response.content)['majors']) == 5
#
#
def test_military_candidate(widget_page, domain_custom_fields, domain_custom_field_categories, domain_aois):
    aoi_string = gen_mock_aois(domain_aois)
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

    url = WidgetApiUrl.CREATE_FOR_TALENT_POOL % widget_page.simple_hash
    post_response = r.post(url, candidate_dict)
    assert post_response.status_code == 201
#
#
# def test_university_candidate(widget_page_fixture, request):
#     aoi_string = gen_mock_aois()
#     candidate_dict = {
#         'name': random_word(12),
#         'emailAdd': '{}@gmail.com'.format(random_word(12)),
#         'city': random_word(10),
#         'state': random_word(10),
#         'university': random_word(10),
#         'degree': random_word(10),
#         'major': random_word(10),
#         'graduation': '{} {}'.format(random_word(8), 2016),
#         'hidden-tags-aoi': aoi_string,
#         'nuid': random_word(8),
#         'jobFrequency': 'Monthly'
#     }
#
#     post_response = r.post(WidgetApiUrl.DOMAIN_WIDGETS
#                            % ('potato', gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
#     assert post_response.status_code == 201
#     # TODO expand to check DB that our fields are there
#     assert 'success' in post_response.content
#
#
# def test_corporate_candidate(widget_page_fixture, request):
#     aoi_string = gen_mock_aois()
#     candidate_dict = {
#         'firstName': random_word(12),
#         'lastName': random_word(12),
#         'emailAdd': '{}@gmail.com'.format(random_word(12)),
#         'hidden-tags-aoi': aoi_string,
#         'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona',
#         'jobFrequency': 'Daily'
#     }
#
#     post_response = r.post(WidgetApiUrl.DOMAIN_WIDGETS
#                            % ('potato', gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
#     assert post_response.status_code == 201
#     # TODO expand to check DB that our fields are there
#     assert 'success' in post_response.content
#
#
# def test_expired_token_refreshes(widget_page_fixture, expired_oauth_credentials, request):
#     aoi_string = gen_mock_aois()
#     candidate_dict = {
#         'firstName': random_word(12),
#         'lastName': random_word(12),
#         'emailAdd': '{}@gmail.com'.format(random_word(12)),
#         'hidden-tags-aoi': aoi_string,
#         'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona',
#         'jobFrequency': 'Daily'
#     }
#
#     post_response = r.post(WidgetApiUrl.DOMAIN_WIDGETS
#                            % ('potato',  gt_url_encrypt(widget_page_fixture.id)), data=candidate_dict)
#     assert post_response.status_code == 201
#     # TODO expand to check DB that our fields are there
#     assert 'success' in post_response.content
#
#
# def test_parse_interest_ids_from_form(request):
#     subcategory = db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).first()
#     parent_category_1 = db.session.query(AreaOfInterest).get(subcategory.parent_id)
#     parent_category_2 = db.session.query(AreaOfInterest).filter(
#         AreaOfInterest.id!=parent_category_1.id).filter(
#         AreaOfInterest.parent_id == None).first()
#     test_string = "{parent_category_without_sub}: All Subcategories|{parent_category_with_sub}: {subcategory}".format(
#         parent_category_without_sub=parent_category_2.name,
#         parent_category_with_sub=parent_category_1.name,
#         subcategory=subcategory.name)
#     processed_ids = parse_interest_ids_from_form(test_string)
#     assert processed_ids == [
#         {'area_of_interest_id': parent_category_2.id}, {'area_of_interest_id': subcategory.id}
#     ]
#
#
# def test_parse_location_ids_from_form(extra_field_fixtures, request):
#     state_custom_field_id = extra_field_fixtures[0].id
#     city_custom_field_id = extra_field_fixtures[1].id
#     test_string = 'Northern California: All Cities|Southern California: Pomona'
#     processed_ids = parse_city_and_state_ids_from_form(test_string)
#     assert processed_ids == [
#         {'id': state_custom_field_id, 'value': 'Northern California'},
#         {'id': city_custom_field_id, 'value': 'Pomona'}
#     ]
#
#
# def test_health_check():
#     import requests
#     response = requests.get(WidgetApiUrl.HEALTH_CHECK)
#     assert response.status_code == 200
#
#     # Testing Health Check URL with trailing slash
#     response = requests.get(WidgetApiUrl.HEALTH_CHECK + '/')
#     assert response.status_code == 200
#
#
def gen_mock_aois(domain_AOIs):
    subcategories = [aoi for aoi in domain_AOIs if aoi.parent_id != None]
    parents_no_sub = [aoi for aoi in domain_AOIs if aoi.parent_id is None]
    all_category_aois = ['{}: All Subcategories'.format(aoi.name) for aoi in parents_no_sub]
    return '|'.join(all_category_aois)
