"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'
# Standard Library.
import datetime
# Third Party
import requests
# Module specific
from widget_service.common.routes import WidgetApiUrl
from widget_service.common.tests.conftest import domain_aois
from widget_service.common.tests.conftest import domain_custom_field_categories
from widget_service.common.tests.conftest import domain_custom_fields
from widget_service.common.tests.conftest import domain_first
from widget_service.common.tests.conftest import first_group
from widget_service.common.tests.conftest import talent_pool
from widget_service.common.tests.conftest import user_first
from widget_service.common.tests.conftest import widget_page
from widget_service.common.utils.handy_functions import random_word


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
    post_response = requests.post(url, candidate_dict)
    assert post_response.status_code == 201


def test_university_candidate(widget_page, domain_custom_fields, domain_custom_field_categories, domain_aois):
    aoi_string = gen_mock_aois(domain_aois)
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

    url = WidgetApiUrl.CREATE_FOR_TALENT_POOL % widget_page.simple_hash
    post_response = requests.post(url, candidate_dict)
    assert post_response.status_code == 201


def test_corporate_candidate(widget_page, domain_custom_fields, domain_custom_field_categories, domain_aois):
    aoi_string = gen_mock_aois(domain_aois)
    candidate_dict = {
        'firstName': random_word(12),
        'lastName': random_word(12),
        'emailAdd': '{}@gmail.com'.format(random_word(12)),
        'hidden-tags-aoi': aoi_string,
        'hidden-tags-location': 'Northern California: All Cities|Southern California: Pomona',
        'jobFrequency': 'Daily'
    }

    url = WidgetApiUrl.CREATE_FOR_TALENT_POOL % widget_page.simple_hash
    post_response = requests.post(url, candidate_dict)
    assert post_response.status_code == 201


def test_health_check():
    response = requests.get(WidgetApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(WidgetApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == 200


def gen_mock_aois(domain_AOIs):
    subcategories = [aoi for aoi in domain_AOIs if aoi.parent_id != None]
    parents_no_sub = [aoi for aoi in domain_AOIs if aoi.parent_id is None]
    all_category_aois = ['{}: All Subcategories'.format(aoi.name) for aoi in parents_no_sub]
    for subcat in subcategories:
        parent = [aoi for aoi in domain_AOIs if aoi.id == subcat.parent_id][0]
        all_category_aois.append('{}: {}'.format(parent.name, subcat.name))
    return '|'.join(all_category_aois)
