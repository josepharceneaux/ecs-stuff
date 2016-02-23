"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import sys

# Application specific imports
from push_campaign_service.tests.test_utilities import (invalid_data_test,
                                                        missing_key_test, OK,
                                                        INVALID_USAGE, FORBIDDEN,
                                                        create_campaign, get_campaign,
                                                        get_campaigns, delete_campaign,
                                                        delete_campaigns)
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test, send_request


URL = PushCampaignApiUrl.CAMPAIGNS


class TestCreateCampaign(object):

    # URL: /v1/campaigns [POST]
    def test_create_campaign_with_invalid_token(self, campaign_data):
        """
        Send request with invalid token and 401 status code is expected
        :param campaign_data: dictionary data for campaign
        :return:
        """
        unauthorize_test('post', URL, 'invalid_token', campaign_data)

    def test_create_campaign_with_invalid_data(self, token_first):
        """
        We will try to create campaign with invalid data (empty, invalid json, without json dump)
        and expect 400 status code
        :param token_first: auth token
        :return:
        """
        invalid_data_test('post', URL, token_first)

    def test_create_campaign_with_missing_fields(self, token_first, campaign_data,
                                                 smartlist_first):
        """
        Here we will try to create campaign with some required fields missing and we will get
        400 status code
        :param token_first: auth token
        :param campaign_data: campaign dictionary data
        :param smartlist_first: smartlist dict object
        :return:
        """
        # First test with missing keys
        for key in ['name', 'body_text', 'url', 'smartlist_ids']:
            data = campaign_data.copy()
            data['smartlist_ids'] = [smartlist_first['id']]
            missing_key_test(data, key, token_first)

    def test_create_campaign(self, token_first, campaign_data, smartlist_first):
        """
        Here we will send a valid data to create a campaign and we are expecting 201 (created)
        :param token_first: auth token
        :param campaign_data: dict data for campaigns
        :param smartlist_first: Smartlist dict object
        :return:
        """
        # Success case. Send a valid data and campaign should be created (201)
        data = campaign_data.copy()
        data['smartlist_ids'] = [smartlist_first['id']]
        response = send_request('post', URL, token_first, data)
        assert response.status_code == 201, 'Push campaign has been created'
        json_response = response.json()
        _id = json_response['id']
        assert json_response['message'] == 'Push campaign was created successfully'
        assert response.headers['Location'] == PushCampaignApiUrl.CAMPAIGN % _id

        # To delete this in finalizer, add id and token
        campaign_data['id'] = _id
        campaign_data['token'] = token_first


class TestGetListOfCampaigns(object):

    # URL: /v1/campaigns/ [GET]
    def test_get_list_with_invalid_token(self):
        """
        We will try to get a list of campaigns with invalid token and
        we are expecting 401 status
        """
        unauthorize_test('get', URL, 'invalid_token')

    # URL: /v1/campaigns [GET]
    def test_get_list_of_one_campaign(self, token_first, campaign_in_db):
        """
        This method tests get list of push campaign created by this user.
        This time we will get one campaign in list that is created by `campaign_in_db` fixture
        :param token_first: auth token
        :param campaign_in_db: push campaign dict object
        :return:
        """
        previous_count = campaign_in_db['previous_count']
        json_response = get_campaigns(token_first)

        assert json_response['count'] == (1 + previous_count), \
            'Campaign Count should be 1 this time'
        assert len(json_response['campaigns']) == (1 + previous_count), 'Got one campaign in list'
        campaign = json_response['campaigns'][previous_count]

        assert campaign['name'] == campaign_in_db['name']
        assert campaign['body_text'] == campaign_in_db['body_text']


class TestDeleteMultipleCampaigns(object):
    """
    This class contains tests for endpoint /v1/campaigns/ and HTTP method DELETE.
    """
    # URL: /v1/campaigns/ [DELETE]

    def test_campaigns_delete_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        unauthorize_test('delete', URL, 'invalid_token')

    def test_campaigns_delete_with_invalid_data(self, token_first):
        """
        Try to delete multiple campaigns using invalid data in body and we will get 400 status code
        :param token_first: auth token
        :return:
        """
        invalid_data_test('delete', URL, token_first)

    def test_campaigns_delete_with_no_data(self, token_first):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        :return:
        """
        delete_campaigns({}, token_first, expected_status=(INVALID_USAGE,))

    def test_campaigns_delete_with_non_json_data(self, token_first):
        """
        User auth token is valid, but non JSON data provided. It should get bad request error.
        :return:
        """
        response = send_request('delete', URL, token_first, data={'ids': [1, 2, 3]}, is_json=False)
        assert response.status_code == INVALID_USAGE

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, token_first, campaign_in_db):
        """
        User auth token is valid, but invalid data provided(other than list).
        ids must be in list format
        It should get bad request error.
        :return:
        """
        data = {'ids': campaign_in_db['id']}
        delete_campaigns(data, token_first, expected_status=(INVALID_USAGE,))

    def test_campaigns_delete_with_invalid_ids(self, token_first):
        """
        User auth token is valid, data is in valid format but ids are not valid
        We are expecting 400 from this request
        :return:
        """
        data = {'ids': [0, 'a', 'b']}
        delete_campaigns(data, token_first, expected_status=(INVALID_USAGE,))

    def test_campaigns_delete_with_authorized_ids(self, token_first, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        :param token_first: auth token
        :param campaign_in_db: campaign created in fixture
        :return:
        """
        data = {'ids': [campaign_in_db['id']]}
        delete_campaigns(data, token_first, expected_status=(OK,))

    def test_campaigns_delete_with_other_user_with_same_domain(self, token_same_domain, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are of those campaigns that
        belong to some other user. It should get unauthorized error.
        :param token_same_domain: auth token
        :param campaign_in_db: campaign created by user_first
        :return:
        """
        data = {'ids': [campaign_in_db['id']]}
        delete_campaigns(data, token_same_domain, expected_status=(OK,))

    def test_campaigns_delete_with_unauthorized_id(self, token_second, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are of those campaigns that
        belong to some other user. It should get unauthorized error.
        :param token_second: auth token for user_second
        :param campaign_in_db: campaign created in fixture
        :return:
        """
        data = {'ids': [campaign_in_db['id']]}
        delete_campaigns(data, token_second, expected_status=(FORBIDDEN,))

    def test_campaigns_delete_authorized_and_unauthorized_ids(self, token_first, campaign_in_db,
                                                              campaign_in_db_second):
        """
        Test with one authorized and one unauthorized SMS campaign. It should get 207
        status code.
        :param token_first: auth token
        :param campaign_in_db: campaign created by user_first
        :param campaign_in_db_second: campaign created by user_second
        :return:
        """
        response = send_request('delete', URL, token_first, data={'ids': [campaign_in_db['id'],
                                                                    campaign_in_db_second['id']]})
        assert response.status_code == 207
        data = {'ids': [campaign_in_db['id'], campaign_in_db_second['id']]}
        delete_campaigns(data, token_first, expected_status=(207,))

    def test_campaigns_delete_with_existing_and_non_existing_ids(self, token_first, campaign_in_db):
        """
        Test with one existing, one invalid id and one non existing ids of SMS campaign.
        It should get 207 status code.
        :param token_first: auth token
        :param campaign_in_db: campaign created by user_first
        """
        invalid_id = sys.maxint
        data = {'ids': [campaign_in_db['id'], invalid_id]}
        delete_campaigns(data, token_first, expected_status=(207,))

    def test_campaigns_delete_with_deleted_record(self, token_first, campaign_in_db):
        """
        We first delete a campaign, and again try to delete it. It should get
        ResourceNotFound error.
        :param token_first: auth token
        :param campaign_in_db: campaign created by user_first
        :return:
        """
        campaign_id = campaign_in_db['id']
        delete_campaign(campaign_id, token_first)
        data = {
            'ids': [campaign_in_db['id']]
        }
        delete_campaigns(data, token_first, expected_status=(404,))






