"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id of SMS Campaign API.
"""
# Standard Imports
import json
import requests

# Service Specific
from werkzeug.security import gen_salt
from sms_campaign_service.custom_exceptions import SmsCampaignApiException

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (UnauthorizedError, ResourceNotFound,
                                                        ForbiddenError, InternalServerError,
                                                        InvalidUsage)


class TestSmsCampaignWithIdHTTPGet(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method GET.

    """

    def test_with_valid_token_and_valid_id(self, auth_token, sms_campaign_of_current_user):
        """
        User auth token is valid. It uses 'sms_campaign_of_current_user' fixture
        to create an SMS campaign in database. It gets that record from GET HTTP request
        Response should be OK. It then assert all fields of record got from GET call with the
        original field values(provided at time of creation of campaign).
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Response should be ok (200)'
        # verify all the field values
        campaign = sms_campaign_of_current_user
        response_campaign = response.json()['campaign']
        assert response_campaign['name'] == campaign.name
        assert response_campaign['body_text'] == campaign.body_text
        assert response_campaign['frequency_id'] == campaign.frequency_id
        assert response_campaign['send_datetime'] == str(campaign.send_datetime)
        assert response_campaign['stop_datetime'] == str(campaign.stop_datetime)

    def test_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_with_id_of_deleted_record(self, auth_token,
                                       sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign and then GETs the record from db.
        It should get ResourceNotFound error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'should get ok response (200)'
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == ResourceNotFound.http_status_code(), \
            'Record should not be found (404)'


class TestSmsCampaignWithIdHTTPPost(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method POST.
    """

    def test_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_with_invalid_header(self, auth_token, sms_campaign_of_current_user):
        """
        User auth token is valid, but content-type is not set.
        it should get bad request error.
        :param auth_token: access token of current user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_with_valid_data(self, valid_header,
                             campaign_valid_data,
                             sms_campaign_of_current_user):
        """
        This uses fixture to create an sms_campaign record in db. It then makes a POST
        call to update that record with name modification. If status code is 200, it then
        gets the record from database and assert the 'name' of modified record.
        :return:
        """
        modified_name = 'Modified Name'
        campaign_valid_data.update({'name': modified_name})
        response_post = requests.post(
            SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
            headers=valid_header,
            data=json.dumps(campaign_valid_data))
        assert response_post.status_code == 200, 'Response should be ok (200)'

        # get updated record to verify the change we made in name
        response_get = requests.get(
            SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
            headers=valid_header,
            data=json.dumps(campaign_valid_data))
        assert response_get.status_code == 200, 'Response should be ok (200)'
        assert response_get.json()['campaign']['name'] == modified_name

    def test_with_id_of_deleted_record(self, valid_header,
                                       sms_campaign_of_current_user,
                                       campaign_valid_data):
        """
        User auth token is valid. It deletes the campaign from database and then tries
        to update the record. It should get ResourceNotFound error.
        :return:
        """
        response_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
            headers=valid_header)
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_post = requests.post(
            SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
            headers=valid_header,
            data=json.dumps(campaign_valid_data))
        assert response_post.status_code == ResourceNotFound.http_status_code(), \
            'Record should not be found (404)'

    def test_with_no_data(self, valid_header,
                          sms_campaign_of_current_user):
        """
        User auth token is valid but no data is provided. It should get bad request error.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                 headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should get bad request error (400)'

    def test_with_non_json_data(self, valid_header, campaign_valid_data,
                                sms_campaign_of_current_user):
        """
        This tries to update SMS campaign record (in sms_campaign table) providing data in dict
        format rather than JSON. It should get bad request error.
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=campaign_valid_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_with_unknown_key_in_data(self, valid_header,
                                      campaign_data_unknown_key_text,
                                      sms_campaign_of_current_user):
        """
        It tries to update the already present sms_campaign record with invalid_data.
        campaign_data_unknown_key_text (fixture) has no 'body_text' (which is mandatory) field
        It should get internal server error. Error code should be 5006.
        :param campaign_data_unknown_key_text: fixture to get invalid data to update old record
        :param sms_campaign_of_current_user: fixture to create sms_campaign record in database
                                            fo current user.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(campaign_data_unknown_key_text))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal server error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MISSING_REQUIRED_FIELD


class TestSmsCampaignWithIdHTTPDelete(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method DELETE.
    """

    def test_delete_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_owned_sms_campaign(self, valid_header, sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign, belong to the user, from database.
        It should get OK response.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                   headers=valid_header)
        assert response.status_code == 200, 'should get ok response (200)'

    def test_not_owned_sms_campaign(self, valid_header, sms_campaign_of_other_user):
        """
        User auth token is valid. It tries to delete the campaign of some other user
        from database. It should get forbidden error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_other_user.id,
                                   headers=valid_header)
        assert response.status_code == ForbiddenError.http_status_code(), \
            'it should get forbidden error (403)'

    def test_with_deleted_campaign(self, valid_header, sms_campaign_of_current_user):
        """
        We first delete an SMS campaign, and again try to delete it. It should get
        ResourceNotFound error.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
                                   headers=valid_header)
        assert response.status_code == 200
        response_after_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
            headers=valid_header)
        assert response_after_delete.status_code == ResourceNotFound.http_status_code()

