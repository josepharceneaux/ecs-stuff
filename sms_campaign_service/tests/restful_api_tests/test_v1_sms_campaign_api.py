"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns of SMS Campaign API.
"""

# Third Party Imports
import json

import requests
from werkzeug.security import gen_salt


# Service Specific
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.tests.conftest import db
from sms_campaign_service.modules.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import assert_for_activity

# Models
from sms_campaign_service.common.models.user import UserPhone

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
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaigns_get_with_no_user_twilio_number(self, auth_token, sample_user):
        """
        User has no Twilio phone number. It should get OK response as we will buy a number for
        user silently.
        :param auth_token: access token of user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        _assert_counts_and_campaigns(response)
        _delete_created_number_of_user(sample_user)

    def test_campaigns_get_with_one_user_twilio_number(self, auth_token,
                                                       user_phone_1):
        """
        User has one Twilio phone number, User already has a Twilio phone number.
        it should get OK response.
        :param auth_token: access token of user
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        _assert_counts_and_campaigns(response)

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
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
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
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
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
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaign_creation_with_no_user_phone_and_valid_data(self, sample_user,
                                                                 campaign_valid_data,
                                                                 valid_header):
        """
        User has no Twilio phone number. It should get Ok response as we will buy a Twilio
        number for user silently.
        :param campaign_valid_data: valid data to create campaign
        :param valid_header: valid header to POST data
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        _assert_campaign_creation(response, sample_user.id, 201)
        _delete_created_number_of_user(sample_user)

    def test_campaign_creation_with_no_data(self,
                                            valid_header,
                                            user_phone_1):
        """
        User has one phone value, but no data was sent. It should get bad request error.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_non_json_data(self, valid_header,
                                                  campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and invalid data type (not JSON) was sent.
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

    def test_campaign_creation_with_unknown_key_in_data( self, campaign_data_unknown_key_text,
                                                         valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (unknown key "text") was sent.
        It should get internal server error. Error code should be 5006.
        :param campaign_data_unknown_key_text: Invalid data to create SMS campaign.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
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
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
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
        It should get InvalidUsage error,
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        campaign_valid_data['smartlist_ids'] = [gen_salt(2)]
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_creation_with_invalid_url_body_text(self, campaign_valid_data,
                                                          valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid URL in body text(random word).
        It should get internal server error, Custom error should be InvalidUrl.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        campaign_valid_data['body_text'] += 'http://' + fake.word()
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_URL_FORMAT

    def test_campaign_creation_with_one_user_phone_and_one_unknown_smartlist(
            self, sample_user, valid_header, campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and valid data. One of the Smartlist ids being sent
        to the server doesn't actually exist in the getTalent's database.
        It should get OK response (207 status code) as code should create campaign for valid
        smartlist ids.
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        campaign_valid_data['smartlist_ids'].append(gen_salt(2))
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        _assert_campaign_creation(response, sample_user.id, 207)

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
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        _assert_campaign_creation(response, sample_user.id, 201)

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
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
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
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaigns_delete_with_invalid_header(self, auth_token):
        """
        User auth token is valid, but no content-type provided in header.
        It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers={'Authorization': 'Bearer %s' % auth_token})
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_no_data(self, valid_header):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS, headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_non_json_data(self, valid_header):
        """
        User auth token is valid, but non JSON data provided. It should get bad request error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data={
                                       'ids': [1, 2, 3]
                                   })
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, valid_header):
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

    def test_campaigns_delete_with_invalid_ids(self, valid_header):
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
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_authorized_ids(self, valid_header, sms_campaign_of_current_user):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
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
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user.id]
                                   }))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'

    def test_campaigns_delete_authorized_and_unauthorized_ids(self, valid_header,
                                                              sms_campaign_of_other_user,
                                                              sms_campaign_of_current_user):
        """
        Test with one authorized and one unauthorized SMS campaign. It should get 207
        status code.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user.id,
                                               sms_campaign_of_current_user.id]
                                   }))
        assert response.status_code == 207
        assert sms_campaign_of_other_user.id in response.json()['not_deleted_ids']

    def test_campaigns_delete_with_deleted_record(self, valid_header, sms_campaign_of_current_user):
        """
        We first delete an SMS campaign, and again try to delete it. It should get
        ResourceNotFound error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user.id]
                                   }))
        assert response.status_code == 200
        response_after_delete = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                                headers=valid_header,
                                                data=json.dumps({
                                                    'ids': [sms_campaign_of_current_user.id]
                                                }))
        assert response_after_delete.status_code == ResourceNotFound.http_status_code()


def _assert_counts_and_campaigns(response, count=0, campaigns=list()):
    """
    This function is used to assert the count of SMS campaigns and list of campaigns
    :param response:
    :param count:
    :param campaigns:
    :return:
    """
    assert response.status_code == 200, 'Status should be Ok (200)'
    assert response.json()
    resp = response.json()
    assert 'count' in resp
    assert 'campaigns' in resp
    assert resp['count'] == count
    assert resp['campaigns'] == campaigns


def _assert_campaign_creation(response, user_id, expected_status_code):
    """
    Here are asserts that make sure that campaign has been created successfully.
    :param response:
    :param user_id:
    :return:
    """
    assert response.status_code == expected_status_code, \
        'It should get status code' + str(expected_status_code)
    assert response.json()
    resp = response.json()
    assert 'location' in response.headers
    assert 'sms_campaign_id' in resp
    assert_for_activity(user_id, ActivityMessageIds.CAMPAIGN_SMS_CREATE, resp['sms_campaign_id'])


def _delete_created_number_of_user(user):
    # Need to commit the session here as we have saved the user_phone in another session.
    # And we do not have any user_phone for this session.
    db.session.commit()
    UserPhone.delete(user.user_phones[0])
