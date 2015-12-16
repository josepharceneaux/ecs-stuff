"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns of SMS Campaign API.
"""

# Third Party Imports
import json
import requests

# Service Specific
from sms_campaign_service.tests.conftest import assert_for_activity
from sms_campaign_service.custom_exceptions import SmsCampaignApiException

# Common Utils
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.utils.activity_utils import CAMPAIGN_SMS_CREATE
from sms_campaign_service.common.error_handling import (UnauthorizedError, InvalidUsage,
                                                        InternalServerError, ForbiddenError)


class TestSmsCampaign(object):
    """
    This class contains tests for endpoint /campaigns/.
    """

    def test_get_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_get_with_valid_token_and_no_user_twilio_number(self, auth_token):
        """
        User has no Twilio phone number. It should get forbidden error.
        :param auth_token: access token of user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == ForbiddenError.http_status_code(),\
            'Should get forbidden error (403)'

    def test_get_with_valid_token_and_one_user_twilio_number(self, auth_token, user_phone_1):
        """
        User has one Twilio phone number, it should get ok response.
        :param auth_token: access token of user
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Status should be Ok (200)'
        assert 'count' in response.json()
        assert 'campaigns' in response.json()
        assert response.json()['count'] == 0
        assert response.json()['campaigns'] == []

    def test_get_with_valid_token_and_user_with_multiple_twilio_numbers(self,
                                                                       auth_token,
                                                                       user_phone_1,
                                                                       user_phone_2):
        """
        User has multiple Twilio phone numbers, it should get internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param auth_token: access token of user
        :param user_phone_1: fixture to assign one test phone number to user
        :param user_phone_2: fixture to assign another test phone number to user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS

    def test_post_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_post_with_invalid_header(self, auth_token):
        """
        User auth token is valid, but content-type is not set.
        it should get bad request error.
        :param auth_token: access token of current user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_post_with_valid_header_and_no_user_phone_and_valid_data(self,
                                                                     campaign_valid_data,
                                                                     valid_header):
        """
        User has no Twilio phone number. It should get forbidden error.
        :param campaign_valid_data: valid data to create campaign
        :param valid_header: valid header to POST data
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'

    def test_post_with_valid_header_and_requesting_new_twilio_number_and_valid_data(
            self, sample_user, valid_header, campaign_valid_data):
        """
        User has no Twilio phone number. Here we request API to buy a number for this user.
        It should save SMS campaign successfully.
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :return:
        """
        campaign_valid_data['buy_new_number'] = True
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 201, 'It should create sms campaign (201)'
        assert 'location' in response.headers
        assert 'id' in response.json()
        assert_for_activity(sample_user.id, CAMPAIGN_SMS_CREATE, response.json()['id'])

    def test_post_with_valid_header_and_one_user_phone_and_no_data(self,
                                                                   valid_header,
                                                                   user_phone_1):
        """
        User has one phone value, but no data. It should get bad request error.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_post_with_valid_header_and_one_user_phone_and_invalid_data_type(self,
                                                                             valid_header,
                                                                             campaign_valid_data,
                                                                             user_phone_1):
        """
        User has one phone value, valid header and invalid data type (not json).
        It should get bad request error.
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=campaign_valid_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_post_with_valid_header_and_one_user_phone_and_invalid_data(self,
                                                                        campaign_invalid_data,
                                                                        valid_header,
                                                                        user_phone_1):
        """
        User has one phone value, valid header and invalid data (unknown key_value).
        It should get internal server error. Error code should be 5006.
        :param campaign_invalid_data: Invalid data to create SMS campaign.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_invalid_data))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal server error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MISSING_REQUIRED_FIELD

    def test_post_with_valid_header_and_one_user_phone_and_valid_data(self,
                                                                      sample_user,
                                                                      valid_header,
                                                                      campaign_valid_data,
                                                                      user_phone_1):
        """
        User has one phone value, valid header and valid data.
        It should get ok response (201 status code)
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 201, 'Should create campaign (201)'
        assert 'location' in response.headers
        assert 'id' in response.json()
        assert_for_activity(sample_user.id, CAMPAIGN_SMS_CREATE, response.json()['id'])

    def test_post_with_valid_header_and_multiple_user_phone_and_valid_data(self,
                                                                           valid_header,
                                                                           campaign_valid_data,
                                                                           user_phone_1,
                                                                           user_phone_2):
        """
        User has multiple Twilio phone numbers, and valid data. It should get internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :param user_phone_2: user_phone fixture to assign another test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code(),\
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS

    def test_delete_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_delete_with_invalid_header(self, auth_token):
        """
        User auth token is valid, but no content-type provided in header.
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers={'Authorization': 'Bearer %s' % auth_token})
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_delete_with_valid_header_and_no_data(self, valid_header):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS, headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(),\
            'It should be a bad request (400)'

    def test_delete_with_valid_header_and_invalid_data(self, valid_header):
        """
        User auth token is valid, but invalid data type provided.
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data={
                                       'ids': [1, 2, 3]
                                   })
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_delete_with_valid_header_and_invalid_data_type(self, valid_header):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': 1
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_delete_with_valid_header_valid_data_type_invalid_ids(self,
                                                                  valid_header):
        """
        User auth token is valid, but invalid data provided(id other than int).
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': ['a', 'b', 1]
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(),\
            'It should be a bad request (400)'

    def test_delete_with_valid_header_valid_data_type_and_valid_ids(self,
                                                                    valid_header,
                                                                    sms_campaign_of_current_user):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be ok.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user.id]
                                   }))
        assert response.status_code == 200, 'Response should be ok (200)'

    def test_delete_with_valid_header_valid_data_type_and_unauthorized_ids(self,
                                                                           valid_header,
                                                                           sms_campaign_of_other_user):
        """
        User auth token is valid, data type is valid and ids are of those sms campaigns that
        belong to some other user. It should get unauthorized error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user.id]
                                   }))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'
