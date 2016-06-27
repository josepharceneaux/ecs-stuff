# User Service app instance
from user_service.user_app import app

# Conftest
from user_service.common.tests.conftest import *

# Models
from user_service.common.models.user import Role

# Helper functions
from user_service.common.routes import UserServiceApiUrl
from user_service.common.utils.test_utils import send_request, response_info

import sys

MAX_INT = sys.maxint
AOIS_URL = UserServiceApiUrl.DOMAIN_AOIS
AOI_URL = UserServiceApiUrl.DOMAIN_AOI
DATA = {"areas_of_interest": [
    {"description": fake.job()}, {"description": fake.job()}, {"description": fake.job()}
]}


class TestCreateDomainAOIS(object):
    METHOD = 'POST'

    def test_add_aois_without_access_token(self, user_first):
        """
        Test: access domain aois resource without access token
        Expect: 401
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()
        resp = send_request(method=self.METHOD, url=AOIS_URL, access_token=None, data=None)
        print response_info(resp)
        assert resp.status_code == requests.codes.UNAUTHORIZED

    def test_add_aois_with_empty_description_field(self, access_token_first, user_first):
        """
        Test: Attempt to add area of interest with empty (None or empty string) value for description field
        Expect: 400; description field is required
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # data with description's value set to None
        data_1 = dict(areas_of_interest=[dict(description=None)])
        resp = send_request(self.METHOD, AOIS_URL, access_token_first, data_1)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD

        # data with description's value set to an empty string
        data_2 = dict(areas_of_interest=[dict(description="")])
        resp = send_request(self.METHOD, AOIS_URL, access_token_first, data_2)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD

        # data with description's value set to whitespaces
        data_3 = dict(areas_of_interest=[dict(description="           ")])
        resp = send_request(self.METHOD, AOIS_URL, access_token_first, data_3)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD

    def test_add_aois_to_domain(self, access_token_first, user_first):
        """
        Test: Add areas of interest to users' domain
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        create_resp = send_request(self.METHOD, AOIS_URL, access_token_first, DATA)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['areas_of_interest']) == len(DATA['areas_of_interest'])
        assert all([aoi.get('id') for aoi in create_resp.json()['areas_of_interest']])

    def test_add_existing_aoi_to_domain(self, access_token_first, domain_aoi, user_first):
        """
        Test: Attempt to an aoi to domain that already exists
        Expect: 400
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Necessary data for test case
        existing_aoi_description = domain_aoi[0].name
        data = dict(areas_of_interest=[dict(description=existing_aoi_description)])

        create_resp = send_request(self.METHOD, AOIS_URL, access_token_first, data)
        json_resp = create_resp.json()
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD

        # AOI ID must be provided in error response
        assert 'id' in json_resp['error']
        existing_aoi_id = json_resp['error']['id']
        assert existing_aoi_id == domain_aoi[0].id

        # Retrieving AOI using the provided ID from the error response should work
        get_resp = send_request('get', AOI_URL % existing_aoi_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['area_of_interest']['domain_id'] == domain_aoi[0].domain_id
        assert get_resp.json()['area_of_interest']['description'] == existing_aoi_description


class TestRetrieveDomainAOIS(object):
    METHOD = 'GET'

    def test_get_domain_aois(self, user_first, access_token_first, domain_aoi):
        """
        Test: Get all of domain's areas of interest
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()
        number_of_aois_in_domain = len(domain_aoi)
        get_resp = send_request(self.METHOD, AOIS_URL, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert len(get_resp.json()['areas_of_interest']) == number_of_aois_in_domain

    def test_get_a_specified_aoi(self, user_first, access_token_first, domain_aoi):
        """
        Test: Get area of interest by providing its ID
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()
        aoi_id = domain_aoi[0].id
        get_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['area_of_interest']['domain_id'] == domain_aoi[0].domain_id
        assert get_resp.json()['area_of_interest']['id'] == aoi_id
        assert get_resp.json()['area_of_interest']['description'] == domain_aoi[0].name

    def test_get_an_aoi_belonging_to_a_diff_domain(self, user_first, access_token_second, domain_aoi):
        """
        Test: Get area of interest of a different domain
        Expect: 403
        """
        user_first.role_id = Role.get_by_name('USER').id
        db.session.commit()
        aoi_id = domain_aoi[0].id
        get_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_second)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.FORBIDDEN


class TestUpdateDomainAOIS(object):
    METHOD = "PUT"

    def test_update_domain_aoi(self, access_token_first, user_first, domain_aoi):
        """
        Test: Update domain's area of interest's description by providing aoi ID via the url
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        aoi_id = domain_aoi[0].id
        update_data = {"areas_of_interest": [{"description": str(uuid.uuid4())[:5]}]}

        # Update area of interest's description
        update_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK
        assert update_resp.json()['areas_of_interest'][0]['id'] == aoi_id

        # Retrieve area of interest & assert its description has been updated
        get_resp = send_request('get', AOI_URL % aoi_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['area_of_interest']['description'] == update_data['areas_of_interest'][0]['description']

    def test_update_domain_aois(self, access_token_first, user_first, domain_aoi):
        """
        Test: Update domain's areas of interest in bulk
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        aoi_1_id, aoi_2_id = domain_aoi[0].id, domain_aoi[1].id
        update_data = {'areas_of_interest': [
            {"id": aoi_1_id, "description": str(uuid.uuid4())[:5]},
            {"id": aoi_2_id, "description": str(uuid.uuid4())[:5]}
        ]}
        update_resp = send_request(self.METHOD, AOIS_URL, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK
        assert len(update_resp.json()['areas_of_interest']) == len(update_data['areas_of_interest'])
        for data in update_resp.json()['areas_of_interest']:
            assert data['id'] in [aoi_1_id, aoi_2_id]

    def test_update_another_domains_aoi(self, access_token_second, user_second, domain_aoi):
        """
        Test: Attempt to update the aoi of a different domain
        Expect: 403
        """
        user_second.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        aoi_id = domain_aoi[0].id
        update_data = {"areas_of_interest": [{"description": str(uuid.uuid4())[:5]}]}
        update_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_second, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.FORBIDDEN

    def test_update_domain_aoi_with_empty_description_field(self, access_token_first, user_first, domain_aoi):
        """
        Test: Update domain aoi without providing the description field
        Expect: 400; description is required
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        aoi_id = domain_aoi[0].id

        # Update with description field set to None
        update_data_1 = {"areas_of_interest": [{"description": None}]}
        updated_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_first, update_data_1)
        print response_info(updated_resp)
        assert updated_resp.status_code == requests.codes.BAD

        # Update with description field set to empty string
        update_data_2 = {"areas_of_interest": [{"description": ""}]}
        updated_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_first, update_data_2)
        print response_info(updated_resp)
        assert updated_resp.status_code == requests.codes.BAD

        # Update with description field set whitespaces
        update_data_3 = {"areas_of_interest": [{"description": "    "}]}
        updated_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_first, update_data_3)
        print response_info(updated_resp)
        assert updated_resp.status_code == requests.codes.BAD

    def test_update_non_existing_aoi(self, access_token_first, user_first):
        """
        Test: Attempt to update an area of interest that doesn't exist
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        update_data = {'areas_of_interest': [{'description': fake.word()}]}
        updated_resp = send_request(self.METHOD, AOI_URL % MAX_INT, access_token_first, update_data)
        print response_info(updated_resp)
        assert updated_resp.status_code == requests.codes.NOT_FOUND


class TestDeleteDomainAOIS(object):
    METHOD = "DELETE"

    def test_delete_domain_aois(self, access_token_first, user_first, domain_aoi):
        """
        Test: Delete all of domain's AOIS
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        domain_aoi_ids = [aoi.id for aoi in domain_aoi]

        # Delete all of domain's AOIS
        del_resp = send_request(self.METHOD, AOIS_URL, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.OK
        assert len(del_resp.json()['areas_of_interest']) == len(domain_aoi)
        assert set([aoi['id'] for aoi in del_resp.json()['areas_of_interest']]) == set(domain_aoi_ids)

        # Domain AOIS should not exists in db anymore
        get_resp = send_request('get', AOIS_URL, access_token_first)
        print response_info(get_resp)
        assert get_resp.json()['areas_of_interest'] == []

    def test_delete_another_domains_aoi(self, access_token_second, user_second, domain_aoi):
        """
        Test: Attempt to delete area of interest of another domain
        Expect: 403; no aoi should be deleted
        """
        user_second.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        aoi_id = domain_aoi[0].id
        del_resp = send_request(self.METHOD, AOI_URL % aoi_id, access_token_second)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.FORBIDDEN

    def test_delete_non_existing_aoi(self, access_token_first, user_first):
        """
        Test: Attempt to delete area of interest that doesn't exist
        Expect: 404
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        del_resp = send_request(self.METHOD, AOI_URL % MAX_INT, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.NOT_FOUND
