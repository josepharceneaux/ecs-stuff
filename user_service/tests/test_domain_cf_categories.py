# User Service app instance
from user_service.user_app import app

import time

# Conftest
from user_service.common.tests.conftest import *

# Helper functions
from user_service.common.routes import UserServiceApiUrl
from user_service.common.utils.test_utils import send_request, response_info
from user_service.common.utils.handy_functions import add_role_to_test_user

# Models
from user_service.common.models.user import DomainRole

CFCS_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELD_CATEGORIES
CFC_URL = UserServiceApiUrl.DOMAIN_CUSTOM_FIELD_CATEGORY


class TestCreateDomainCustomFieldCategories(object):
    def test_create_domain_ccf_category(self, user_first, access_token_first):
        """
        Test: Create a single custom field category for user's domain
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS,
                                           DomainRole.Roles.CAN_GET_DOMAINS])

        data = {'custom_field_categories': [{'name': str(uuid.uuid4())[:8]}]}
        create_resp = send_request('post', CFCS_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve custom field categories
        custom_field_category_id = create_resp.json()['custom_field_categories'][0]['id']
        get_resp = send_request('get', CFC_URL % custom_field_category_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK

        retrieved_data = get_resp.json()['custom_field_category']
        assert retrieved_data['id'] == custom_field_category_id
        assert retrieved_data['domain_id'] == user_first.domain_id
        assert retrieved_data['name'] == data['custom_field_categories'][0]['name']

    def test_create_domain_ccf_categories(self, user_first, access_token_first):
        """
        Test: Create multiple custom field categories for user's domain
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS])

        data = {'custom_field_categories': [
            {'name': str(uuid.uuid4())[:8]}, {'name': str(uuid.uuid4())[:8]}, {'name': str(uuid.uuid4())[:8]}
        ]}
        create_resp = send_request('post', CFCS_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['custom_field_categories']) == len(data['custom_field_categories'])
        assert [cfc.get('id') for cfc in create_resp.json()['custom_field_categories']]


class TestCreateInvalidDomainCustomFieldCategories(object):
    """
    Class contains functional tests that will result in the following errors
        - json schema violation (400)
        - invalid data (400)
        - unauthorized access (401)
        - forbidden access (403)
        - non existing data (404)
    """

    def test_create_cfc_without_setting_users_permission(self, access_token_first):
        """
        Test: Attempt to access endpoint without setting user's permissions (can edit domain)
        Expect: 401; unauthorized error
        """
        data = {}  # data is irrelevant since we expect an unauthorized error to be raised early on

        # POST /v1/custom_field_categories
        resp = send_request('post', CFCS_URL, access_token_first, data)
        assert resp.status_code == requests.codes.UNAUTHORIZED

    def test_create_cfc_with_bad_token(self, user_first, access_token_first):
        """
        Test: Attempt to access endpoint using:
            1. An expired token
            2. An invalid token
            3. no token
        Expect: 401; unauthorized error
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS])

        # Set access_token_first's expiration to 10 seconds ago
        token = Token.get_token(access_token_first)
        token.expires = datetime.fromtimestamp(time.time() - 10)
        db.session.commit()

        data = {}  # data is irrelevant since we expect an unauthorized error to be raised early on

        # Create using an expired access token
        create_resp = send_request('post', CFCS_URL, access_token_first, data)
        assert create_resp.status_code == requests.codes.UNAUTHORIZED

        # Create using an invalid access token
        invalid_access_token = access_token_first + '{}'.format(random.randint(1, 9))
        create_resp = send_request('post', CFCS_URL, invalid_access_token, data)
        assert create_resp.status_code == requests.codes.UNAUTHORIZED

        # Create using no access token
        create_resp = send_request('post', CFCS_URL, None, data)
        assert create_resp.status_code == requests.codes.UNAUTHORIZED

    def test_create_cfc_without_providing_category_name(self, user_first, access_token_first):
        """
        Test: Attempt to create custom field category without providing category name using four different approaches:
            1. Omit the 'name' key
            2. Set name value to None
            3. Set name value to empty string
            4. set name value to a bunch of whitespace
        Expect: 400; name is a required field
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS])

        name = [None, '', '         ']  # name values considered "empty" by the API

        data = {'custom_field_categories': [{}]}
        create_resp = send_request('post', CFCS_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD

        data = {'custom_field_categories': [{'name': random.choice(name)}]}
        create_resp = send_request('post', CFCS_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD


class TestGetDomainCustomFieldCategories(object):
    def test_get_domain_custom_field_categories(self, user_first, access_token_first, domain_custom_field_categories):
        """
        Test: Retrieve all custom field categories belonging to user's domain
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_DOMAINS])

        get_resp = send_request('get', CFCS_URL, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK

        # Count of custom field categories sent in should equal to count of custom field categories retrieved
        retrieved_data = get_resp.json()['custom_field_categories']
        assert len(retrieved_data) == len(domain_custom_field_categories)

        # All custom field categories should belong to the same domain
        cfc_domain_id = set([data['domain_id'] for data in retrieved_data])
        assert len(cfc_domain_id) == 1, 'All custom field categories should belong to the same domain'
        assert cfc_domain_id.pop() == user_first.domain_id

        category_names_sent_in = [category.name for category in domain_custom_field_categories]
        category_names_retrieved = [category['name'] for category in retrieved_data]
        assert category_names_retrieved == category_names_sent_in

    def test_get_custom_field_category(self, user_first, access_token_first, domain_custom_field_categories):
        """
        Test: Retrieve a custom field category by providing its ID
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_DOMAINS])

        cfc_id = domain_custom_field_categories[0].id
        get_resp = send_request('get', CFC_URL % cfc_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK

        retrieved_data = get_resp.json()['custom_field_category']
        assert retrieved_data['id'] == cfc_id
        assert retrieved_data['domain_id'] == user_first.domain_id
        assert retrieved_data['name'] == domain_custom_field_categories[0].name


class TestGetInvalidDomainCustomFieldCategories(object):
    """
    Class contains functional tests that will result in the following errors
        - unauthorized access (401)
        - forbidden access (403)
        - non existing data (404)
    """

    def test_get_cfc_without_setting_users_permission(self, access_token_first):
        """
        Test: Attempt to access endpoint without setting user's permissions (can get domain)
        Expect: 401; unauthorized error
        """
        # GET /v1/custom_field_categories/:id
        cfc_id = '5'  # ID is irrelevant since we expect an unauthorized error to be raised early on
        resp = send_request('get', CFC_URL % cfc_id, access_token_first)
        assert resp.status_code == requests.codes.UNAUTHORIZED
        resp = send_request('get', CFCS_URL, access_token_first)
        assert resp.status_code == requests.codes.UNAUTHORIZED

    def test_get_cfc_with_bad_token(self, user_first, access_token_first):
        """
        Test: Attempt to access endpoint using:
            1. An expired token
            2. An invalid token
            3. no token
        Expect: 401; unauthorized error
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_DOMAINS])

        # Set access_token_first's expiration to 10 seconds ago
        token = Token.get_token(access_token_first)
        token.expires = datetime.fromtimestamp(time.time() - 10)
        db.session.commit()

        cfc_id = '5'  # ID is irrelevant since we expect an unauthorized error to be raised early on

        # Retrieve using an expired access token
        get_resp = send_request('get', CFCS_URL, access_token_first)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED
        get_resp = send_request('get', CFC_URL % cfc_id, access_token_first)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED

        # Retrieve using an invalid access token
        invalid_access_token = access_token_first + '{}'.format(random.randint(1, 9))
        get_resp = send_request('get', CFCS_URL, invalid_access_token)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED
        get_resp = send_request('get', CFC_URL % cfc_id, invalid_access_token)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED

        # Retrieve using no access token
        get_resp = send_request('get', CFCS_URL, None)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED
        get_resp = send_request('get', CFC_URL % cfc_id, None)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED

    def test_get_cfc_from_forbidden_domain(self, user_second, access_token_second, domain_custom_field_categories):
        """
        Test: Attempt to retrieve custom field categories of a domain not belonging to user
        """
        add_role_to_test_user(user_second, [DomainRole.Roles.CAN_GET_DOMAINS])

        get_resp = send_request('get', CFC_URL % domain_custom_field_categories[0].id, access_token_second)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.FORBIDDEN


class TestUpdateDomainCustomFieldCategories(object):
    def test_update_cf_category(self, user_first, access_token_first, domain_custom_field_categories):
        """
        Test: Update a single custom field category
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS, DomainRole.Roles.CAN_GET_DOMAINS])

        # cf-category id & domain ID before update
        cf_category_id = domain_custom_field_categories[0].id
        cf_category_domain_id = domain_custom_field_categories[0].domain_id

        update_data = {'custom_field_category': {'name': fake.word()}}

        # Update a single cf-category
        update_resp = send_request('put', CFC_URL % cf_category_id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.json()['custom_field_category']['id'] == cf_category_id

        # Retrieve updated cf-category
        get_resp = send_request('get', CFC_URL % cf_category_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.json()['custom_field_category']['id'] == cf_category_id, \
            'cf-category ID should remain unchanged'
        assert get_resp.json()['custom_field_category']['domain_id'] == cf_category_domain_id, \
            'cf-category domain ID should remain unchanged'
        assert get_resp.json()['custom_field_category']['name'] == update_data['custom_field_category']['name']

    def test_update_cf_categories(self, user_first, access_token_first, domain_custom_field_categories):
        """
        Test: Update multiple custom field categories
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS, DomainRole.Roles.CAN_GET_DOMAINS])

        # cf-categories IDs & domain IDs
        cf_category_ids = [cf_category.id for cf_category in domain_custom_field_categories]
        cf_category_domain_ids = [cf_category.domain_id for cf_category in domain_custom_field_categories]

        update_data = {'custom_field_categories': [
            {'id': cf_category_ids[0], 'name': str(uuid.uuid4())[:5]},
            {'id': cf_category_ids[1], 'name': str(uuid.uuid4())[:5]},
            {'id': cf_category_ids[2], 'name': str(uuid.uuid4())[:5]}
        ]}

        # Update domain custom field categories
        update_resp = send_request('put', CFCS_URL, access_token_first, update_data)
        assert update_resp.status_code == requests.codes.OK

        # Retrieve updated custom field categories
        get_resp = send_request('get', CFCS_URL, access_token_first)
        print response_info(get_resp)

        retrieved_categories = get_resp.json()['custom_field_categories']

        # Updated custom field category IDs, domain IDs, and names
        updated_cf_category_ids = [cf_category['id'] for cf_category in retrieved_categories]
        updated_cf_category_domain_ids = [cf_category['domain_id'] for cf_category in retrieved_categories]
        updated_cf_category_names = [cf_category['name'] for cf_category in retrieved_categories]

        assert set(updated_cf_category_ids).issubset(cf_category_ids), 'cf-category IDs should remain unchanged'
        assert set(updated_cf_category_domain_ids).issubset(cf_category_domain_ids), \
            'cf-category domain IDs should remain unchanged'
        assert set(updated_cf_category_names).issubset([d['name'] for d in update_data['custom_field_categories']])


class TestUpdateInvalidDomainCustomFieldCategories(object):
    """
    Class contains functional tests that will result in the following errors
        - unauthorized access (401)
        - forbidden access (403)
        - non existing data (404)
    """

    def test_update_cfc_without_setting_users_permission(self, access_token_first):
        """
        Test: Attempt to access endpoint without setting user's permissions (can get domain)
        Expect: 401; unauthorized error
        """
        # PUT /v1/custom_field_categories/:id
        cfc_id = '5'  # ID is irrelevant since we expect an unauthorized error to be raised early on
        resp = send_request('put', CFC_URL % cfc_id, access_token_first)
        assert resp.status_code == requests.codes.UNAUTHORIZED
        resp = send_request('put', CFCS_URL, access_token_first)
        assert resp.status_code == requests.codes.UNAUTHORIZED

    def test_update_cfc_with_bad_token(self, user_first, access_token_first):
        """
        Test: Attempt to access endpoint using:
            1. An expired token
            2. An invalid token
            3. no token
        Expect: 401; unauthorized error
        """
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_DOMAINS])

        # Set access_token_first's expiration to 10 seconds ago
        token = Token.get_token(access_token_first)
        token.expires = datetime.fromtimestamp(time.time() - 10)
        db.session.commit()

        update_data = {}  # Data is irrelevant since we expect an unauthorized error to be raised early on
        cfc_id = '5'  # ID is irrelevant since we expect an unauthorized error to be raised early on

        # Update using an expired access token
        update_resp = send_request('put', CFCS_URL, access_token_first, update_data)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED
        update_resp = send_request('put', CFC_URL % cfc_id, access_token_first, update_data)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED

        # Update using an invalid access token
        invalid_access_token = access_token_first + '{}'.format(random.randint(1, 9))
        update_resp = send_request('put', CFCS_URL, invalid_access_token, update_data)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED
        update_resp = send_request('put', CFC_URL % cfc_id, invalid_access_token, update_data)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED

        # Update using no access token
        update_resp = send_request('put', CFCS_URL, None, update_data)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED
        update_resp = send_request('put', CFC_URL % cfc_id, None, update_data)
        assert update_resp.status_code == requests.codes.UNAUTHORIZED

    def test_update_cfc_from_forbidden_domain(self, user_second, access_token_second, domain_custom_field_categories):
        """
        Test: Attempt to update custom field categories of a domain not belonging to user
        """
        add_role_to_test_user(user_second, [DomainRole.Roles.CAN_EDIT_DOMAINS])

        update_data = {'custom_field_category': {'name': 'virus'}}

        update_data = send_request('put', CFC_URL % domain_custom_field_categories[0].id,
                                   access_token_second, update_data)
        print response_info(update_data)
        assert update_data.status_code == requests.codes.FORBIDDEN
