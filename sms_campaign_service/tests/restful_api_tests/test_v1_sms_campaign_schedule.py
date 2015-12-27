"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/schedule of SMS Campaign API.
"""

# Third Party Imports
import json
import requests
from werkzeug.security import gen_salt

# Service Specific
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.tests.conftest import db, CAMPAIGN_SCHEDULE_DATA
from sms_campaign_service.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import assert_for_activity, \
    assert_method_not_allowed, assert_campaign_schedule

# Models
from sms_campaign_service.common.models.user import UserPhone

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.utils.activity_utils import ActivityMessageIds
from sms_campaign_service.common.error_handling import (UnauthorizedError, InvalidUsage,
                                                        InternalServerError, ForbiddenError,
                                                        ResourceNotFound)


class TestSmsCampaignSchedule(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/schedule.
    """

    def test_for_get_request(self, auth_token, sms_campaign_of_current_user):
        """
        GET method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert_method_not_allowed(response, 'GET')

    def test_for_delete_request(self, auth_token, sms_campaign_of_current_user):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert_method_not_allowed(response, 'DELETE')

    def test_campaign_schedule(self, valid_header, sms_campaign_of_current_user):
        """
        This is test to schedule SMS campaign with all valid parameters. This should get OK
         response
        """
        # Try to schedule deleted campaign
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(CAMPAIGN_SCHEDULE_DATA))
        assert_campaign_schedule(response)

    def test_campaign_schedule_with_no_auth_header(self, auth_token, sms_campaign_of_current_user):
        """
        Using no Auth header like dict(Authorization='Bearer %s' % 'invalid_token'),
        just passing auth token as str. It should get Attribute Error.
        :return:
        """
        try:

            requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                          headers=auth_token)
        except AttributeError as e:
            assert 'unicode' in e.message

    def test_campaign_schedule_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaign_schedule_with_invalid_header(self, auth_token, sms_campaign_of_current_user):
        """
        Making POST call with no content-type specifying.
        It should get bad request error.
        :return:
        """

        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_invalid_datetime(self, valid_header,
                                                     sms_campaign_of_current_user):
        """
        User has one phone value, valid header and invalid data (Invalid Datetime).
        It should get internal server error, Custom error should be InvalidDatetime.
        :param valid_header: valid header to POST data
        :return:
        """
        data = CAMPAIGN_SCHEDULE_DATA.copy()
        data['send_datetime'] = data['send_datetime'].split('Z')[0]
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InternalServerError.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_DATETIME

    def test_campaign_schedule_with_non_existing_frequency_id(self, valid_header,
                                                              sms_campaign_of_current_user):
        """
        Trying to schedule a campaign with invalid frequency Id, Valid ids are in [1,2,3..6] for
        now.
        :return:
        """
        data = CAMPAIGN_SCHEDULE_DATA.copy()
        data['frequency_id'] = fake.numerify()  # this returns a three digit random number
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        _assert_invalid_frequency_id(response)

    def test_campaign_schedule_with_invalid_frequency_id(self, valid_header,
                                                         sms_campaign_of_current_user):
        """
        Trying to schedule a campaign with non int frequency Id, It should get bad request error,
        :return:
        """
        data = CAMPAIGN_SCHEDULE_DATA.copy()
        data['frequency_id'] = fake.word()
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        _assert_invalid_frequency_id(response)

    def test_campaign_schedule_with_not_owned_campaign(self, valid_header,
                                                       sms_campaign_of_other_user):
        """
        Trying to schedule a campaign of some other user, It should get forbidden error,
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_other_user.id,
                                 headers=valid_header,
                                 data=json.dumps(CAMPAIGN_SCHEDULE_DATA))
        assert response.status_code == ForbiddenError.http_status_code()

    def test_campaign_schedule_with_non_json_data_type(self, valid_header,
                                                       sms_campaign_of_current_user):
        """
        Trying to schedule a campaign of with Non JSON data, It should get bad request error,
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=CAMPAIGN_SCHEDULE_DATA)
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_no_data(self, valid_header, sms_campaign_of_current_user):
        """
        Trying to schedule a campaign of with no data, It should get bad request error,
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_deleted_resource(self, valid_header,
                                                     sms_campaign_of_current_user):
        """
        Here we first delete the campaign from database. Then we try to schedule it. It
        should get ResourceNotFound error,
        """
        # Delete the campaign first
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                   headers=valid_header)
        assert response.status_code == 200
        # Try to schedule deleted campaign
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(CAMPAIGN_SCHEDULE_DATA))
        assert response.status_code == ResourceNotFound.http_status_code()


def _assert_invalid_frequency_id(response):
    """
    This asserts that given response get the custom exception InvalidFrequencyId
    :param response:
    :return:
    """
    assert response.status_code == InternalServerError.http_status_code()
    assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_FREQUENCY_ID
