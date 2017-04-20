"""
This module contains tests for custom field search endpoint
"""
# 3rd party imports
import requests
# Common imports
from user_service.common.constants import CUSTOM_FIELD_TYPES, PRE_DEFINED, INPUT
from user_service.common.tests.api_conftest import *
# Service specific imports
from user_service.modules.constants import NUMBER_OF_SAVED_CUSTOM_FIELDS


class TestDomainCustomFieldSearch(object):
    URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS

    def test_search_custom_fields_with_no_keyword(self, token_domain_admin):
        """
        Test: Searches Domain Custom Fields with no keyword passed it should return all domain custom fields
        """
        response = send_request('get', self.URL, token_domain_admin)
        assert response.status_code == requests.codes.ok
        data = response.json()['custom_fields']
        assert len(data) == NUMBER_OF_SAVED_CUSTOM_FIELDS[INPUT] + NUMBER_OF_SAVED_CUSTOM_FIELDS[PRE_DEFINED]

    def test_search_result_order(self, token_domain_admin):
        """
        Test: Searches custom fields with param sort_by and sort_type
        """
        response = send_request('get', self.URL, token_domain_admin, params={'sort_by': 'name'})
        assert response.status_code == requests.codes.ok
        data = response.json()['custom_fields']

        first_cf = data[0]
        response = send_request('get', self.URL, token_domain_admin, params={'sort_by': 'name', 'sort_type': 'ASC'})
        data = response.json()['custom_fields']
        assert first_cf == data[-1]

    def test_search_result_with_a_keyword(self, token_domain_admin):
        """
        Test: Search a custom field against a name
        """
        response = send_request('get', self.URL, token_domain_admin, params={'query': 'NUID'})
        assert response.status_code == requests.codes.ok
        data = response.json()['custom_fields']
        assert len(data) == 1

    def test_search_custom_field_type(self, token_domain_admin):
        """
        Test: Search a custom field against type
        """
        response = send_request('get', self.URL, token_domain_admin, params={'type': CUSTOM_FIELD_TYPES[PRE_DEFINED]})
        assert response.status_code == requests.codes.ok
        data = response.json()['custom_fields']
        assert len(data) == NUMBER_OF_SAVED_CUSTOM_FIELDS[PRE_DEFINED]

        response = send_request('get', self.URL, token_domain_admin, params={'type': CUSTOM_FIELD_TYPES[INPUT]})
        assert response.status_code == requests.codes.ok
        data = response.json()['custom_fields']
        assert len(data) == NUMBER_OF_SAVED_CUSTOM_FIELDS[INPUT]

        response = send_request('get', self.URL, token_domain_admin, params={'type': 'all'})
        assert response.status_code == requests.codes.ok
        data = response.json()['custom_fields']
        assert len(data) == NUMBER_OF_SAVED_CUSTOM_FIELDS[INPUT] + NUMBER_OF_SAVED_CUSTOM_FIELDS[PRE_DEFINED]
