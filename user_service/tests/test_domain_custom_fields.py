# User Service app instance
from user_service.user_app import app

# Conftest
from user_service.common.tests.conftest import *

# Helper functions
from user_service.common.routes import UserServiceApiUrl
from user_service.common.utils.test_utils import send_request, response_info

# Models
from user_service.common.models.user import Role

import sys


class TestCreateDomainCustomFields(object):
    URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS

    def test_add_custom_fields_without_access_token(self, user_first):
        """
        Test:  Access end point without an access token
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()
        resp = send_request('post', self.URL, None, {})
        print response_info(resp)
        assert resp.status_code == requests.codes.UNAUTHORIZED

    def test_add_custom_fields_with_whitespaced_name(self, access_token_first, user_first):
        """
        Test: Attempt to create a custom field with empty
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()
        data = {'custom_fields': [{'name': '   '}]}
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD

    def test_add_custom_fields_to_domain(self, access_token_first, user_first):
        """
        Test:  Add custom fields to domain
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Create domain custom fields
        data = {'custom_fields': [{'name': str(uuid.uuid4())[:5]}, {'name': str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)

        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['custom_fields']) == len(data['custom_fields'])
        assert 'id' in create_resp.json()['custom_fields'][0]

    def test_add_duplicate_custom_fields_to_domain(self, access_token_first, user_first):
        """
        Test:  Add identical custom fields to the same domain
        Expect:  201, but only one should be created
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        name = str(uuid.uuid4())[:5]
        data = {'custom_fields': [{'name': name}, {'name': name}]}

        # Create domain custom fields
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD


class TestGetDomainCustomFields(object):
    CFS_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS
    CF_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELD

    def test_get_custom_fields_without_access_token(self):
        """
        Test:  Access end point without an access token
        """
        get_resp = send_request('get', self.CFS_URL, None)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED


    def test_get_domains_custom_fields(self, access_token_first, user_first, domain_custom_fields):
        """
        Test:  Retrieve domain custom fields
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()

        # Retrieve all of domain's custom fields
        get_resp = send_request('get', self.CFS_URL, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert len(get_resp.json()['custom_fields']) == len(domain_custom_fields)
        assert set([cf['id'] for cf in get_resp.json()['custom_fields']]).issubset(
            [cf.id for cf in domain_custom_fields])

    def test_get_custom_field_by_id(self, user_first, access_token_first, domain_custom_fields):
        """
        Test: Retrieve domain custom field by ID
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()

        custom_field_id = domain_custom_fields[0].id

        # Retrieve custom field by id
        get_resp = send_request('get', self.CF_URL % custom_field_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['custom_field']['id'] == custom_field_id
        assert get_resp.json()['custom_field']['domain_id'] == user_first.domain_id
        assert get_resp.json()['custom_field']['name'] == domain_custom_fields[0].name

    def test_get_custom_field_of_another_domain(self, access_token_second, domain_custom_fields):
        """
        Test: Retrieve custom fields of another domain
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()

        custom_field_id = domain_custom_fields[0].id

        # Retrieve another domain's custom field
        get_resp = send_request('get', self.CF_URL % custom_field_id, access_token_second)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.FORBIDDEN

    def test_get_non_existing_custom_field(self, user_first, access_token_first):
        """
        Test: Retrieve custom field using an id that is not recognized
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()

        non_existing_cf_id = sys.maxint

        get_resp = send_request('get', self.CF_URL % non_existing_cf_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.NOT_FOUND


class TestUpdateDomainCustomFields(object):
    CFS_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS
    CF_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELD

    def test_update_custom_fields_without_access_token(self):
        """
        Test:  Access endpoint without an access token
        """
        update_resp = send_request('put', self.CFS_URL, None)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED

    def test_update_domains_custom_fields(self, access_token_first, user_first, domain_custom_fields):
        """
        Test:  Update domain custom fields
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Update all of domain's custom fields
        data = {'custom_fields': [
            {'id': domain_custom_fields[0].id, 'name': str(uuid.uuid4())[:5]},
            {'id': domain_custom_fields[1].id, 'name': str(uuid.uuid4())[:5]}
        ]}
        update_resp = send_request('put', self.CFS_URL, access_token_first, data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK
        assert len(update_resp.json()['custom_fields']) == len(domain_custom_fields)
        assert set([cf['id'] for cf in update_resp.json()['custom_fields']]).issubset(
            [cf.id for cf in domain_custom_fields])

    def test_update_custom_field_by_id(self, user_first, access_token_first, domain_custom_fields):
        """
        Test: Update domain custom field by ID
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        custom_field_id = domain_custom_fields[0].id

        # Update custom field by id
        data = {'custom_field': {'id': domain_custom_fields[0].id, 'name': str(uuid.uuid4())[:5]}}
        update_resp = send_request('put', self.CF_URL % custom_field_id, access_token_first, data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK
        assert update_resp.json()['custom_field']['id'] == custom_field_id

        # Retrieve custom field and assert on its updated name
        get_resp = send_request('get', self.CF_URL % custom_field_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['custom_field']['name'] != domain_custom_fields[0].name
        assert get_resp.json()['custom_field']['name'] == data['custom_field']['name']

    def test_update_custom_field_of_another_domain(self, user_second, access_token_second, domain_custom_fields):
        """
        Test: Update custom fields of another domain
        """
        user_second.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        custom_field_id = domain_custom_fields[0].id

        # Update another domain's custom field
        data = {'custom_field': {'id': domain_custom_fields[0].id, 'name': str(uuid.uuid4())[:5]}}
        update_resp = send_request('put', self.CF_URL % custom_field_id, access_token_second, data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.FORBIDDEN

    def test_update_non_existing_custom_field(self, user_first, access_token_first):
        """
        Test: Update custom field using an id that is not recognized
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        non_existing_cf_id = sys.maxint

        data = {'custom_field': {'name': str(uuid.uuid4())[:5]}}
        update_resp = send_request('put', self.CF_URL % non_existing_cf_id, access_token_first, data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.NOT_FOUND


# TODO: uncomment the TestDeleteDomainCustomFields when DELETE /v1/custom_fields is created - Amir
# class TestDeleteDomainCustomFields(object):
#     CFS_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELDS
#     CF_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELD
#
#     def test_delete_custom_fields_without_access_token(self):
#         """
#         Test:  Access end point without an access token
#         """
#         del_resp = send_request('delete', self.CFS_URL, None)
#         print response_info(del_resp)
#         assert del_resp.status_code == requests.codes.UNAUTHORIZED
#
#     def test_delete_custom_field_without_user_permission(self, access_token_first):
#         """
#         Test: Access endpoint without user's appropriate permission
#         """
#         del_resp = send_request('delete', self.CFS_URL, access_token_first)
#         print response_info(del_resp)
#         assert del_resp.status_code == requests.codes.UNAUTHORIZED
#
#     def test_delete_custom_field_by_id(self, user_first, access_token_first, domain_custom_fields):
#         """
#         Test: Delete domain custom field by ID
#         """
#         user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#         db.session.commit()
#
#         custom_field_id = domain_custom_fields[0].id
#
#         # Delete custom field by id
#         del_resp = send_request('delete', self.CF_URL % custom_field_id, access_token_first)
#         print response_info(del_resp)
#         assert del_resp.status_code == requests.codes.OK
#         assert del_resp.json()['custom_field']['id'] == custom_field_id
#
#     def test_delete_custom_field_of_another_domain(self, user_second, access_token_second, domain_custom_fields):
#         """
#         Test: Delete custom fields of another domain
#         """
#         user_second.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#         db.session.commit()
#
#         custom_field_id = domain_custom_fields[0].id
#
#         # Delete another domain's custom field
#         del_resp = send_request('delete', self.CF_URL % custom_field_id, access_token_second)
#         print response_info(del_resp)
#         assert del_resp.status_code == requests.codes.FORBIDDEN
#
#     def test_delete_non_existing_custom_field(self, user_first, access_token_first):
#         """
#         Test: Delete custom field using an ID that is not recognized
#         """
#         user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#         db.session.commit()
#
#         non_existing_cf_id = sys.maxint
#
#         del_resp = send_request('delete', self.CF_URL % non_existing_cf_id, access_token_first)
#         print response_info(del_resp)
#         assert del_resp.status_code == requests.codes.NOT_FOUND

