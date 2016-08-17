"""
This module contains test for API endpoint
        /v1/push-campaigns

In these tests, we will try to create, get and delete
push campaigns with different scenarios

Create Campaign: /v1/push-campaigns [POST]
    - with invalid token
    - with invalid data (empty body, invalid json, without json headers)
    - with missing required fields in data
    - with valid data

Get Campaigns: /v1/push-campaigns [GET]
    - with invalid token
    - with valid token

Delete Multiple Campaigns: /v1/push-campaigns [DELETE]
    - with invalid token
    - with invalid data (empty body, invalid json, without json headers)
    - with valid format but without json dumps
    - with non list ids
    - with non existing ids
    - with valid data
    - with different user from same domain
    - with different user from different domain
    - with campaign ids for different domains
    - with a campaign id that has been deleted
"""
# Builtin imports
import sys

# 3rd party imports
from requests import codes

# Application specific imports
from push_campaign_service.modules.push_campaign_base import PushCampaignBase
from push_campaign_service.tests.test_utilities import (create_campaign, get_campaigns,
                                                        delete_campaign, delete_campaigns)
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from push_campaign_service.common.utils.test_utils import (send_request, invalid_data_test, missing_keys_test,
                                                           unexpected_field_test, invalid_value_test)
from push_campaign_service.common.utils.api_utils import MAX_PAGE_SIZE


URL = PushCampaignApiUrl.CAMPAIGNS


class TestCreateCampaign(object):

    # URL: /v1/push-campaigns [POST]
    def test_create_campaign_with_invalid_token(self, campaign_data):
        """
        Send request with invalid token and 401 status code is expected
        :param campaign_data: dictionary data for campaign
        """
        create_campaign(campaign_data, 'invalid_token', expected_status=(codes.UNAUTHORIZED,))

    def test_create_campaign_with_invalid_data(self, token_first):
        """
        We will try to create campaign with invalid data (empty, invalid json, without json dump)
        and expect 400 status code
        :param token_first: auth token
        """
        invalid_data_test('post', URL, token_first)

    def test_create_campaign_with_unexpected_field(self, token_first, campaign_data, smartlist_first):
        """
        Create a campaign with an extra unexpected field, API should raise InvalidUsage 400
        :param string token_first: auth token
        :param dict campaign_data: data to create campaign
        :param dict smartlist_first: Smartlist object
        """
        campaign_data['smartlist_ids'] = [smartlist_first['id']]
        unexpected_field_test('post', URL, campaign_data, token_first)

    def test_create_campaign_with_missing_fields(self, token_first, campaign_data, smartlist_first):
        """
        Here we will try to create campaign with some required fields missing and we will get
        400 status code
        :param string token_first: auth token
        :param dict campaign_data: data to create campaign
        :param dict smartlist_first: Smartlist object
        """
        # First test with missing keys
        campaign_data['smartlist_ids'] = [smartlist_first['id']]
        missing_keys_test(URL, campaign_data, PushCampaignBase.REQUIRED_FIELDS, token_first)

    def test_campaign_creation_with_invalid_body_text(self, token_first, campaign_data, smartlist_first):
        """
        Create a campaign with invalid body text, it should raise InvalidUsage 400
        :param string token_first: auth token
        :param dict campaign_data: data to create campaign
        :param dict smartlist_first: Smartlist object
        """
        campaign_data['smartlist_ids'] = [smartlist_first['id']]
        invalid_values = ['', '  ', {}, [], None, True]
        invalid_value_test(URL, campaign_data, 'body_text', invalid_values, token_first)

    def test_campaign_creation_with_invalid_smartlist_ids(self, token_first, campaign_data):
        """
        Create campaign with invalid smartlist ids, API should raise InvalidUsage 400
        :param string token_first: auth token
        :param dict campaign_data: data to create campaign
        """
        invalid_ids = CampaignsTestsHelpers.INVALID_ID
        invalid_value_test(URL, campaign_data, 'smartlist_ids', invalid_ids, token_first)

    def test_campaign_creation_with_invalid_name(self, token_first, campaign_data, smartlist_first):
        """
        Create a campaign with invalid name field, API should raise InvalidUsage 400
        :param string token_first: auth token
        :param dict campaign_data: data to create campaign
        :param dict smartlist_first: Smartlist object
        """
        campaign_data['smartlist_ids'] = [smartlist_first['id']]
        invalid_names = [0, -1, None, True, '', '    ']
        invalid_value_test(URL, campaign_data, 'name', invalid_names, token_first)

    def test_create_campaign(self, token_first, campaign_data, smartlist_first):
        """
        Here we will send a valid data to create a campaign and we are expecting 201 (created)
        :param string token_first: auth token
        :param dict campaign_data: data to create campaign
        :param dict smartlist_first: Smartlist object
        """
        # Success case. Send a valid data and campaign should be created (201)
        data = campaign_data.copy()
        data['smartlist_ids'] = [smartlist_first['id']]
        response = create_campaign(data, token_first, expected_status=(codes.CREATED,))
        _id = response['id']
        assert response['message'] == 'Push campaign was created successfully'
        assert response['headers']['Location'] == PushCampaignApiUrl.CAMPAIGN % _id

        # To delete this in finalizer, add id and token
        campaign_data['id'] = _id
        campaign_data['token'] = token_first


class TestGetListOfCampaigns(object):

    # URL: /v1/push-campaigns/ [GET]
    def test_get_list_with_invalid_token(self):
        """
        We will try to get a list of campaigns with invalid token and
        we are expecting 401 status
        """
        get_campaigns('invalid_token', expected_status=(codes.UNAUTHORIZED,))

    # URL: /v1/push-campaigns [GET]
    def test_get_campaigns_pagination(self, token_first, campaigns_for_pagination_test):
        """
        In this test, we will test that pagination is working as expected for campaigns endpoint.
        :param token_first: auth token
        :param campaigns_for_pagination_test: campaigns count
        """
        total_count = campaigns_for_pagination_test
        per_page = total_count - 5
        response = get_campaigns(token_first, per_page=per_page, expected_status=(codes.OK,))
        assert len(response['campaigns']) == per_page

        per_page = total_count
        response = get_campaigns(token_first, per_page=per_page, expected_status=(codes.OK,))
        assert len(response['campaigns']) == per_page

        per_page = MAX_PAGE_SIZE + 1
        get_campaigns(token_first, per_page=per_page, expected_status=(codes.BAD_REQUEST,))

    def test_get_all_campaigns_in_user_domain(self, token_first, token_same_domain, token_second,
                                              campaign_in_db, campaign_in_db_same_domain, campaign_in_db_second,
                                              ):
        """
        In this test, we will create three campaign for three users , two from same domain and one from
        different domain and then we will get campaigns using user_first token and we will expect two campaigns,
        and one campaign when using token for `user_second`.
        :return:
        """
        created_campaign_ids = {campaign_in_db['id'], campaign_in_db_same_domain['id']}
        response = get_campaigns(token_first, expected_status=(codes.OK,))
        assert created_campaign_ids.issubset({campaign['id'] for campaign in response['campaigns']})

        response = get_campaigns(token_same_domain, expected_status=(codes.OK,))
        assert created_campaign_ids.issubset({campaign['id'] for campaign in response['campaigns']})

        response = get_campaigns(token_second, expected_status=(codes.OK,))
        assert {campaign_in_db_second['id']}.issubset({campaign['id'] for campaign in response['campaigns']})


class TestDeleteMultipleCampaigns(object):
    """
    This class contains tests for endpoint /v1/push-campaigns/ and HTTP method DELETE.
    """
    # URL: /v1/push-campaigns/ [DELETE]

    def test_campaigns_delete_with_invalid_token(self, campaign_in_db):
        """
        User auth token is invalid, it should get Unauthorized.
        """
        data = {
            'ids': [campaign_in_db['id']]
        }
        delete_campaigns(data, 'invalid_token', expected_status=(codes.UNAUTHORIZED,))

    def test_campaigns_delete_with_invalid_data(self, token_first):
        """
        Try to delete multiple campaigns using invalid data in body and we will get 400 status code
        :param token_first: auth token
        """
        invalid_data_test('delete', URL, token_first)

    def test_campaigns_delete_with_non_json_data(self, token_first):
        """
        User auth token is valid, but non JSON data provided. It should get bad request error.
        """
        response = send_request('delete', URL, token_first, data={'ids': [1, 2, 3]}, is_json=False)
        assert response.status_code == codes.BAD_REQUEST

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, token_first, campaign_in_db):
        """
        User auth token is valid, but invalid data provided(other than list).
        ids must be in list format
        It should get bad request error.
        """
        data = {'ids': campaign_in_db['id']}
        delete_campaigns(data, token_first, expected_status=(codes.BAD_REQUEST,))

    def test_campaigns_delete_with_invalid_ids(self, token_first):
        """
        User auth token is valid, data is in valid format but ids are not valid
        We are expecting 400 from this request
        """
        data = {'ids': [0, 'a', 'b']}
        delete_campaigns(data, token_first, expected_status=(codes.BAD_REQUEST,))

    def test_campaigns_delete_with_authorized_ids(self, token_first, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        :param token_first: auth token
        :param campaign_in_db: campaign created in fixture
        """
        data = {'ids': [campaign_in_db['id']]}
        delete_campaigns(data, token_first, expected_status=(codes.OK,))

    def test_campaigns_delete_with_other_user_with_same_domain(self, token_same_domain, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are of those campaigns that
        belong to some other user. It should get unauthorized error.
        :param token_same_domain: auth token
        :param campaign_in_db: campaign created by user_first
        """
        data = {'ids': [campaign_in_db['id']]}
        delete_campaigns(data, token_same_domain, expected_status=(codes.OK,))

    def test_campaigns_delete_with_unauthorized_id(self, token_second, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are of those campaigns that
        belong to some other user. It should get unauthorized error.
        :param token_second: auth token for user_second
        :param campaign_in_db: campaign created in fixture
        """
        data = {'ids': [campaign_in_db['id']]}
        delete_campaigns(data, token_second, expected_status=(codes.FORBIDDEN,))

    def test_campaigns_delete_authorized_and_unauthorized_ids(self, token_first, campaign_in_db,
                                                              campaign_in_db_second):
        """
        Test with one authorized and one unauthorized push campaign. It should get 403
        status code.
        :param token_first: auth token
        :param campaign_in_db: campaign created by user_first
        :param campaign_in_db_second: campaign created by user_second
        """
        response = send_request('delete', URL, token_first, data={'ids': [campaign_in_db['id'],
                                                                          campaign_in_db_second['id']]})
        assert response.status_code == codes.FORBIDDEN
        data = {'ids': [campaign_in_db['id'], campaign_in_db_second['id']]}
        delete_campaigns(data, token_first, expected_status=(codes.FORBIDDEN,))

    def test_campaigns_delete_with_existing_and_non_existing_ids(self, token_first, campaign_in_db):
        """
        Test with one existing, one invalid id and one non existing ids of push campaign.
        It should get 404 status code.
        :param token_first: auth token
        :param campaign_in_db: campaign created by user_first
        """
        non_existing_id = sys.maxint
        data = {'ids': [campaign_in_db['id'], non_existing_id]}
        delete_campaigns(data, token_first, expected_status=(codes.NOT_FOUND,))

    def test_campaigns_delete_with_deleted_record(self, token_first, campaign_in_db):
        """
        We first delete a campaign, and again try to delete it. It should get
        ResourceNotFound error.
        :param token_first: auth token
        :param campaign_in_db: campaign created by user_first
        """
        campaign_id = campaign_in_db['id']
        delete_campaign(campaign_id, token_first)
        data = {
            'ids': [campaign_in_db['id']]
        }
        delete_campaigns(data, token_first, expected_status=(codes.NOT_FOUND,))
