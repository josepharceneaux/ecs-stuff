"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns of SMS Campaign API.
"""

# Third Party Imports
import json
import requests

# Service Specific
from werkzeug.security import gen_salt
from sms_campaign_service.tests.conftest import assert_for_activity
from sms_campaign_service.custom_exceptions import SmsCampaignApiException

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.utils.activity_utils import ActivityMessageIds
from sms_campaign_service.common.error_handling import (UnauthorizedError, InvalidUsage,
                                                        InternalServerError, ForbiddenError,
                                                        ResourceNotFound)


class TestSmsCampaignHTTPGet(object):
    """
    This class contains tests for endpoint /campaigns/ and HTTP method GET.
    """

    def test_campaigns_get_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaigns_get_with_no_user_twilio_number(self, auth_token):
        """
        User has no Twilio phone number. It should get forbidden error.
        :param auth_token: access token of user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'Should get forbidden error (403)'

    def test_campaigns_get_with_one_user_twilio_number(self, auth_token,
                                                       user_phone_1):
        """
        User has one Twilio phone number, it should get OK response.
        :param auth_token: access token of user
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Status should be Ok (200)'
        assert 'count' in response.json()
        assert 'campaigns' in response.json()
        assert response.json()['count'] == 0
        assert response.json()['campaigns'] == []

    def test_campaigns_get_with_user_having_multiple_twilio_numbers(self,
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
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS


class TestSmsCampaignHTTPPost(object):
    """
    This class contains tests for endpoint /campaigns/ and HTTP method POST.
    """

    def test_campaign_creation_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaign_creation_with_invalid_header(self, auth_token):
        """
        User auth token is valid, but content-type is not set.
        it should get bad request error.
        :param auth_token: access token of current user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaign_creation_with_no_user_phone_and_valid_data(self,
                                                                 campaign_valid_data,
                                                                 valid_header):
        """
        User has no Twilio phone number. It should get forbidden error.
        :param campaign_valid_data: valid data to create campaign
        :param valid_header: valid header to POST data
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'

    def test_campaign_creation_by_requesting_new_twilio_number(self, sample_user,
                                                               valid_header, campaign_valid_data):
        """
         User has no Twilio phone number. Our code should save SMS campaign successfully
        (by buying the number behind the scenes).
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :return:
        """
        campaign_valid_data['buy_new_number'] = True
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 201, 'It should create SMS campaign (201)'
        assert 'location' in response.headers
        assert 'sms_campaign_id' in response.json()
        assert_for_activity(sample_user.id, ActivityMessageIds.CAMPAIGN_SMS_CREATE,
                            response.json()['sms_campaign_id'])

    def test_campaign_creation_with_no_data(self,
                                                             valid_header,
                                                             user_phone_1):
        """
        User has one phone value, but no data was sent. It should get bad request error.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_invalid_data_type(self, valid_header,
                                                      campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and invalid data type (not json) was sent.
        It should get bad request error.
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=campaign_valid_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_unknown_key_in_data(
            self, campaign_data_unknown_key_text, valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (unknown key "text") was sent.
        It should get internal server error. Error code should be 5006.
        :param campaign_data_unknown_key_text: Invalid data to create SMS campaign.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_data_unknown_key_text))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal server error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MISSING_REQUIRED_FIELD
        assert 'body_text' in response.json()['error']['message']

    def test_campaign_creation_with_missing_key_smartlist_ids_in_data(
            self, campaign_data_missing_smartlist_ids, valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (Missing key "smartlist_ids").
        It should get internal server error. Error code should be 5006.
        :param campaign_data_missing_smartlist_ids: Invalid data to create SMS campaign.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_data_missing_smartlist_ids))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal server error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MISSING_REQUIRED_FIELD
        assert 'smartlist_ids' in response.json()['error']['message']

    def test_campaign_creation_with_one_user_phone_and_unknown_smartlist_ids(
            self, campaign_valid_data, valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (Unknown "smartlist_ids").
        It should get ResourceNotFound error,
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        campaign_valid_data['smartlist_ids'] = [gen_salt(2)]
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == ResourceNotFound.http_status_code()

    def test_campaign_creation_with_one_user_phone_and_invalid_datetime(self,
                                                                      campaign_valid_data,
                                                                      valid_header,
                                                                      user_phone_1):
        """
        User has one phone value, valid header and invalid data (Invalid Datetime).
        It should get internal server error, Custom error should be InvalidDatetime.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        campaign_valid_data['send_datetime'] = campaign_valid_data['send_datetime'].split('Z')[0]
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_DATETIME

    def test_campaign_creation_with_one_user_phone_and_one_unknown_smartlist(
            self, sample_user, valid_header, campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and valid data.Smart list being sent to the server
        doesn't actually exist in the getTalent's database.
        It should get OK response (201 status code)
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        campaign_valid_data['smartlist_ids'].append(gen_salt(2))
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 207, \
            'Should create campaign, but one smartlist is not found(207)'
        assert 'location' in response.headers
        assert 'sms_campaign_id' in response.json()
        assert_for_activity(sample_user.id, ActivityMessageIds.CAMPAIGN_SMS_CREATE,
                            response.json()['sms_campaign_id'])

    def test_campaign_creation_with_one_user_phone_and_valid_data(self,

                                                                  sample_user,
                                                                  valid_header,
                                                                  campaign_valid_data,
                                                                  user_phone_1):
        """
        User has one phone value, valid header and valid data.
        It should get OK response (201 status code)
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 201, 'Should create campaign (201)'
        assert 'location' in response.headers
        assert 'sms_campaign_id' in response.json()
        assert_for_activity(sample_user.id, ActivityMessageIds.CAMPAIGN_SMS_CREATE,
                            response.json()['sms_campaign_id'])

    def test_campaign_creation_with_multiple_user_phone_and_valid_data(self,
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
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS


class TestSmsCampaignHTTPDelete(object):
    """
    This class contains tests for endpoint /campaigns/ and HTTP method DELETE.
    """

    def test_campaigns_delete_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaigns_delete_with_invalid_header(self, auth_token):
        """
        User auth token is valid, but no content-type provided in header.
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers={'Authorization': 'Bearer %s' % auth_token})
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_no_data(self, valid_header):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL, headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_invalid_data(self, valid_header):
        """
        User auth token is valid, but invalid data type provided.
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers=valid_header,
                                   data={
                                       'ids': [1, 2, 3]
                                   })
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_invalid_data_type(self, valid_header):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': 1
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_invalid_ids(self, valid_header):
        """
        User auth token is valid, but invalid data provided(id other than int).
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': ['a', 'b', 1]
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_authorized_ids(self, valid_header, sms_campaign_of_current_user):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user.id]
                                   }))
        assert response.status_code == 200, 'Response should be ok (200)'

    def test_campaigns_delete_with_unauthorized_ids(self, valid_header,
                                                    sms_campaign_of_other_user):
        """
        User auth token is valid, data type is valid and ids are of those SMS campaigns that
        belong to some other user. It should get unauthorized error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS_URL,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user.id]
                                   }))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'
