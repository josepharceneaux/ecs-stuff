"""
Test cases for CandidateCustomFieldResource
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

import sys

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles, get_response
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

VALUE = fake.word()
MAX_INT = sys.maxint
URL = CandidateApiUrl.CUSTOM_FIELDS


class TestCreateCandidateCustomField(object):
    def test_add_and_retrieve_candidate_custom_field(self, access_token_first, user_first, domain_custom_fields,
                                                     candidate_first):
        """
        Test:  Add candidate custom field & retrieve it
        Expect:  201
        """
        AddUserRoles.add_get_edit(user_first)
        data = {'candidate_custom_fields': [
            {'custom_field_id': domain_custom_fields[0].id, 'value': VALUE}]
        }

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate custom field via ID
        ccf_id = create_resp.json()['candidate_custom_fields'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CUSTOM_FIELD % (candidate_first.id, ccf_id), access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['candidate_custom_field']['value'] == data['candidate_custom_fields'][0]['value'].strip()

    def test_add_candidate_custom_field_with_whitespaced_value(self, access_token_first, user_first,
                                                               domain_custom_fields,
                                                               candidate_first):
        """
        Test:  Add candidate custom field with a value that contains whitespaces
        Expect:  201, whitespace must be removed before inserting into db
        """
        AddUserRoles.add_get_edit(user_first)
        data = {'candidate_custom_fields': [
            {'custom_field_id': domain_custom_fields[0].id, 'value': ' ' + VALUE + ' '}]
        }

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate custom field via ID
        ccf_id = create_resp.json()['candidate_custom_fields'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CUSTOM_FIELD % (candidate_first.id, ccf_id), access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['candidate_custom_field']['custom_field_id'] == domain_custom_fields[0].id
        assert get_resp.json()['candidate_custom_field']['value'] == data['candidate_custom_fields'][0]['value'].strip()

    def test_add_candidate_custom_field_with_no_value(self, access_token_first, user_first,
                                                      domain_custom_fields,
                                                      candidate_first):
        """
        Test:  Add candidate custom field with a value that contains whitespaces
        Expect:  400
        """
        AddUserRoles.add_get_edit(user_first)
        data = {'candidate_custom_fields': [{'custom_field_id': domain_custom_fields[0].id}]}

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD

    def test_add_using_unauthorized_user_domain(self, access_token_second, user_second, domain_custom_fields,
                                                candidate_first):
        """
        Test:  Attempt to add candidate custom field using an unauthorized custom field ID
        Expect:  403
        """
        AddUserRoles.edit(user_second)
        data = {'candidate_custom_fields': [{'custom_field_id': domain_custom_fields[0].id, 'value': VALUE}]}

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id,
                                   access_token_second, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.FORBIDDEN
        assert create_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_add_using_invalid_custom_field_id(self, access_token_first, user_first, candidate_first):
        """
        Test:  Attempt to add candidate custom field with non-existing custom field ID
        Expect:  404
        """
        AddUserRoles.edit(user_first)
        data = {'candidate_custom_fields': [{'custom_field_id': MAX_INT, 'value': VALUE}]}

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.NOT_FOUND
        assert create_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_NOT_FOUND


class TestGetCandidateCustomField(object):
    def test_get_ccf_of_forbidden_candidate(self, access_token_first, user_first, domain_custom_fields,
                                            candidate_first, candidate_second):
        """
        Test:  Attempt to retrieve the ccf of a different candidate
        Expect: 403
        """
        AddUserRoles.add_get_edit(user_first)
        data = {'candidate_custom_fields': [{'custom_field_id': domain_custom_fields[0].id, 'value': VALUE}]}

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Retrieve ccf using a different candidate ID
        ccf_id = create_resp.json()['candidate_custom_fields'][0]['id']
        url = CandidateApiUrl.CUSTOM_FIELD % (candidate_second.id, ccf_id)
        get_resp = send_request('get', url, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.FORBIDDEN
        assert get_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_FORBIDDEN

    def test_get_non_existing_ccf(self, access_token_first, user_first, candidate_first):
        """
        Test:  Attempt to retrieve a ccf that isn't yet created
        Expect: 404
        """
        AddUserRoles.add_get_edit(user_first)

        # Retrieve ccf
        get_resp = send_request('get', CandidateApiUrl.CUSTOM_FIELD % (candidate_first.id, MAX_INT), access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.NOT_FOUND
        assert get_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_NOT_FOUND

    def test_get_ccf_outside_of_users_domain(self, access_token_second, user_second, domain_custom_fields,
                                             user_second_candidate, candidate_first, user_first, access_token_first):
        """
        Test:  Attempt to retrieve ccf that do not belong to user's domain
        Expect: 403
        """
        AddUserRoles.all_roles(user_second)
        AddUserRoles.all_roles(user_first)

        # Create candidate custom field
        data = {'candidate_custom_fields': [{'custom_field_id': domain_custom_fields[0].id, 'value': VALUE}]}
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Retrieve candidate custom field
        url = CandidateApiUrl.CUSTOM_FIELD % (user_second_candidate.id, domain_custom_fields[0].id)
        get_resp = get_response('get', url, access_token_second, requests.codes.FORBIDDEN)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.FORBIDDEN
        assert get_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_FORBIDDEN


class TestDeleteCandidateCustomField(object):
    def test_delete_ccf_of_forbidden_candidate(self, access_token_first, user_first, domain_custom_fields,
                                               candidate_first, candidate_second):
        """
        Test:  Attempt to delete the ccf of a different candidate
        Expect: 403
        """
        AddUserRoles.all_roles(user_first)
        data = {'candidate_custom_fields': [{'custom_field_id': domain_custom_fields[0].id, 'value': VALUE}]}

        # Add candidate custom fields for candidate
        create_resp = send_request('post', URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Retrieve ccf using a different candidate ID
        ccf_id = create_resp.json()['candidate_custom_fields'][0]['id']
        url = CandidateApiUrl.CUSTOM_FIELD % (candidate_second.id, ccf_id)
        del_resp = send_request('delete', url, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.FORBIDDEN
        assert del_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_FORBIDDEN

    def test_delete_non_existing_ccf(self, access_token_first, user_first, candidate_first):
        """
        Test:  Attempt to delete a ccf that isn't yet created
        Expect: 404
        """
        AddUserRoles.all_roles(user_first)

        # Retrieve ccf
        url = CandidateApiUrl.CUSTOM_FIELD % (candidate_first.id, MAX_INT)
        del_resp = send_request('delete', url, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.NOT_FOUND
        assert del_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_NOT_FOUND

    def test_delete_ccf_outside_of_users_domain(self, access_token_second, user_second,
                                                domain_custom_fields, user_second_candidate):
        """
        Test:  Attempt to delete ccf that do not belong to user's domain
        Expect: 403
        """
        AddUserRoles.all_roles(user_second)
        url = CandidateApiUrl.CUSTOM_FIELD % (user_second_candidate.id, domain_custom_fields[0].id)
        del_resp = get_response('delete', url, access_token_second, requests.codes.FORBIDDEN)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.FORBIDDEN
        assert del_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_FORBIDDEN
