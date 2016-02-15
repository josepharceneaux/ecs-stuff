"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports

# Application specific imports
from push_campaign_service.tests.test_utilities import (invalid_data_test,
                                                        unauthorize_test,
                                                        missing_key_test,
                                                        send_request, OK,
                                                        INVALID_USAGE, FORBIDDEN)
from push_campaign_service.common.routes import PushCampaignApiUrl


URL = PushCampaignApiUrl.CAMPAIGNS


class TestCreateCampaign(object):

    # URL: /v1/campaigns [POST]
    def test_create_campaign_with_invalid_token(self, campaign_data):
        unauthorize_test('post', URL, 'invalid_token', campaign_data)

    def test_create_campaign_with_invalid_data(self, token):
        invalid_data_test('post', URL, token)

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
        response = send_request('post', URL, token, data)
        assert response.status_code == 201, 'Push campaign has been created'
        json_response = response.json()
        _id = json_response['id']
        assert json_response['message'] == 'Push campaign was created successfully'
        assert response.headers['Location'] == PushCampaignApiUrl.CAMPAIGN % _id
        campaign_data['id'] = _id


class TestGetListOfCampaigns(object):

    # URL: /v1/campaigns/ [GET]
    def test_get_list_with_invalid_token(self):
        unauthorize_test('get', URL, 'invalid_token')

    def test_get_list_of_zero_campaigns(self, token):
        """
        This method tests get list of push campaign created by this user.
        At this point, test user has no campaign created, so we will get an empty list
        :param token: auth token
        :return:
        """
        response = send_request('get', URL, token)
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
        response = send_request('get', URL, token)
        assert response.status_code == OK, 'Status code ok'
        json_response = response.json()

        assert json_response['count'] == 1, 'Campaign Count should be 1 this time'
        assert len(json_response['campaigns']) == 1, 'Got one campaign in list'
        campaign = json_response['campaigns'][0]
        assert campaign_in_db.body_text == campaign['body_text']
        assert campaign_in_db.name == campaign['name']
        assert campaign_in_db.url == campaign['url']


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

    def test_campaigns_delete_with_invalid_data(self, token):
        """
        User auth token is invalid data
        :return:
        """
        invalid_data_test('delete', URL, token)

    def test_campaigns_delete_with_no_data(self, token):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        :return:
        """
        response = send_request('delete', URL, token, data={})
        assert response.status_code == INVALID_USAGE

    def test_campaigns_delete_with_non_json_data(self, token):
        """
        User auth token is valid, but non JSON data provided. It should get bad request error.
        :return:
        """
        response = send_request('delete', URL, token, data={'ids': [1, 2, 3]}, is_json=False)
        assert response.status_code == INVALID_USAGE

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, token):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should get bad request error.
        :return:
        """
        response = send_request('delete', URL, token, data={'ids': 1})
        assert response.status_code == INVALID_USAGE

    def test_campaigns_delete_with_invalid_ids(self, token):
        """
        User auth token is valid, data is in valid format but ids are not valid
        We are expecting 400 from this request
        :return:
        """
        response = send_request('delete', URL, token, data={'ids': [0, 'a', 'b']})
        assert response.status_code == INVALID_USAGE

    def test_campaigns_delete_with_authorized_ids(self, token, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        :return:
        """
        response = send_request('delete', URL, token, data={'ids': [campaign_in_db.id]})
        assert response.status_code == OK

    def test_campaigns_delete_with_other_user_with_same_domain(self, token2, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are of those campaigns that
        belong to some other user. It should get unauthorized error.
        :return:
        """
        response = send_request('delete', URL, token2, data={'ids': [campaign_in_db.id]})
        assert response.status_code == OK

    def test_campaigns_delete_with_unauthorized_id(self, token_for_different_domain, campaign_in_db):
        """
        User auth token is valid, data type is valid and ids are of those campaigns that
        belong to some other user. It should get unauthorized error.
        :return:
        """
        response = send_request('delete', URL, token_for_different_domain, data={'ids': [campaign_in_db.id]})
        assert response.status_code == FORBIDDEN

    # def test_delete_campaigns_of_multiple_users(self, valid_header, user_first,
    #                                             campaign_of_other_user_in_same_domain,
    #                                             campaign_of_current_user):
    #     """
    #     Test with one authorized and one unauthorized campaign. It should get 207
    #     status code.
    #     :return:
    #     """
    #     pass

    def test_campaigns_delete_authorized_and_unauthorized_ids(self, token_first, campaign_in_db,
                                                              campaign_in_db_second):
        """
        Test with one authorized and one unauthorized SMS campaign. It should get 207
        status code.
        :return:
        """
        response = send_request('delete', URL, token_first, data={'ids': [campaign_in_db.id,
                                                                    campaign_in_db_second['id']]})
        assert response.status_code == 207
    #
    # def test_campaigns_delete_with_existing_and_non_existing_ids(self, valid_header, user_first,
    #                                                              sms_campaign_of_current_user):
    #     """
    #     Test with one existing, one invalid id and one non existing ids of SMS campaign.
    #     It should get 207 status code.
    #     :return:
    #     """
    #     last_id = CampaignsCommonTests.get_last_id(SmsCampaign)
    #     response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
    #                                headers=valid_header,
    #                                data=json.dumps({
    #                                    'ids': [last_id, sms_campaign_of_current_user.id]
    #                                }))
    #     assert response.status_code == 207
    #     assert last_id in response.json()['not_found_ids']
    #     assert_for_activity(user_first.id, ActivityMessageIds.CAMPAIGN_DELETE,
    #                         sms_campaign_of_current_user.id)
    #
    # def test_campaigns_delete_with_valid_and_invalid_ids(self, valid_header, user_first,
    #                                                      sms_campaign_of_current_user):
    #     """
    #     Test with one valid, and one invalid id of SMS campaign.
    #     It should get 207 status code.
    #     :return:
    #     """
    #     response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
    #                                headers=valid_header,
    #                                data=json.dumps({
    #                                    'ids': [0, sms_campaign_of_current_user.id]
    #                                }))
    #     assert response.status_code == 207
    #     assert 0 in response.json()['not_deleted_ids']
    #     assert_for_activity(user_first.id, ActivityMessageIds.CAMPAIGN_DELETE,
    #                         sms_campaign_of_current_user.id)
    #
    # def test_campaigns_delete_with_deleted_record(self, valid_header, user_first,
    #                                               sms_campaign_of_current_user):
    #     """
    #     We first delete an SMS campaign, and again try to delete it. It should get
    #     ResourceNotFound error.
    #     :return:
    #     """
    #     campaign_id = sms_campaign_of_current_user.id
    #     response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
    #                                headers=valid_header,
    #                                data=json.dumps({
    #                                    'ids': [campaign_id]
    #                                }))
    #     assert_campaign_delete(response, user_first.id, campaign_id)
    #     response_after_delete = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
    #                                             headers=valid_header,
    #                                             data=json.dumps({
    #                                                 'ids': [campaign_id]
    #                                             }))
    #     assert response_after_delete.status_code == ResourceNotFound.http_status_code()







