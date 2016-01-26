"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports

# Application specific imports
from push_campaign_service.tests.test_utilities import (invalid_data_test,
                                                        unauthorize_test,
                                                        missing_key_test,
                                                        send_request, OK)
from push_campaign_service.common.routes import PushCampaignApiUrl


class TestCreateCampaign(object):

    # URL: /v1/campaigns [POST]
    def test_create_campaign_with_invalid_token(self, campaign_data):
        unauthorize_test('post', PushCampaignApiUrl.CAMPAIGNS, 'invalid_token', campaign_data)

    def test_create_campaign_with_invalid_data(self, token):
        invalid_data_test('post', PushCampaignApiUrl.CAMPAIGNS, token)

    def test_create_campaign_with_missing_fields(self, token, campaign_data,
                                                 test_smartlist):
        # First test with missing keys
        for key in ['name', 'body_text', 'url', 'smartlist_ids']:
            data = campaign_data.copy()
            data['smartlist_ids'] = [test_smartlist.id]
            missing_key_test(data, key, token)

    def test_create_campaign(self, token, campaign_data, test_smartlist):
        """
        This method tests push campaign creation endpoint.

        :param auth_data: token, validity_status
        :param campaign_data: dict
        :param test_smartlist: Smartlist
        :return:
        """
        # Success case. Send a valid data and campaign should be created (201)
        data = campaign_data.copy()
        data['smartlist_ids'] = [test_smartlist.id]
        response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
        assert response.status_code == 201, 'Push campaign has been created'
        json_response = response.json()
        _id = json_response['id']
        assert json_response['message'] == 'Push campaign was created successfully'
        assert response.headers['Location'] == PushCampaignApiUrl.CAMPAIGN % _id
        campaign_data['id'] = _id


class TestGetListOfCampaigns(object):

    # URL: /v1/campaigns/ [GET]
    def test_get_list_with_invalid_token(self):
        unauthorize_test('get', PushCampaignApiUrl.CAMPAIGNS, 'invalid_token')

    def test_get_list_of_zero_campaigns(self, token):
        """
        This method tests get list of push campaign created by this user.
        At this point, test user has no campaign created, so we will get an empty list
        :param token: auth token
        :return:
        """
        response = send_request('get', PushCampaignApiUrl.CAMPAIGNS, token)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()

        assert json_response['count'] == 0, 'Campaign Count should be 0 this time'
        assert len(json_response['campaigns']) == 0, 'Got an empty list of campaigns'

    # URL: /v1/campaigns [GET]
    def test_get_list_of_one_campaign(self, token, campaign_in_db):
        """
        This method tests get list of push campaign created by this user.
        This time we will get one campaign in list that is created by `campaign_in_db` fixture
        :param token: auth token
        :type token: str
        :param campaign_in_db: push campaign object
        :type campaign_in_db: PushCampaign
        :return:
        """
        response = send_request('get', PushCampaignApiUrl.CAMPAIGNS, token)
        assert response.status_code == OK, 'Status code ok'
        json_response = response.json()

        assert json_response['count'] == 1, 'Campaign Count should be 1 this time'
        assert len(json_response['campaigns']) == 1, 'Got one campaign in list'
        campaign = json_response['campaigns'][0]
        assert campaign_in_db.body_text == campaign['body_text']
        assert campaign_in_db.name == campaign['name']
        assert campaign_in_db.url == campaign['url']










