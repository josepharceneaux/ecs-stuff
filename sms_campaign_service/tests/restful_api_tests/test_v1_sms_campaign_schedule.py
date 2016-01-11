"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/schedule of SMS Campaign API.
"""

# Third Party Imports
import json
import requests
from datetime import datetime
from datetime import timedelta

# Service Specific
from sms_campaign_service.common.campaign_services.campaign_utils import FrequencyIds
from sms_campaign_service.common.tests.auth_utilities import to_utc_str
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.tests.modules.common_functions import assert_method_not_allowed

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (UnauthorizedError, InvalidUsage,
                                                        ForbiddenError,
                                                        ResourceNotFound)


class TestSmsCampaignSchedule(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/schedule.
    """
    # TODO: add tests for re-schedule and stop campaign
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

    def test_campaign_schedule_with_no_start_datetime(self, valid_header,
                                                      sms_campaign_of_current_user):
        """
        This is test to schedule SMS campaign with no start datetime. This should get
        forbidden error.
        """
        data = generate_campaign_schedule_data()
        del data['start_datetime']
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_past_date(self, valid_header, sms_campaign_of_current_user):
        """
        This is test to schedule SMS campaign with past datetime. This should get forbidden error.
        """
        data = generate_campaign_schedule_data()
        data['end_datetime'] = to_utc_str(datetime.utcnow() - timedelta(days=1))
        data['frequency_id'] = FrequencyIds.DAILY
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

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
        It should get bad request error
        :param valid_header: valid header to POST data
        :return:
        """
        data = generate_campaign_schedule_data()
        data['start_datetime'] = data['start_datetime'].split('Z')[0]
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_non_existing_frequency_id(self, valid_header,
                                                              sms_campaign_of_current_user):
        """
        Trying to schedule a campaign with invalid frequency Id, Valid ids are in [1,2,3..6] for
        now. It should get bad request error.
        :return:
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = fake.numerify()  # this returns a three digit random number
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_invalid_frequency_id(self, valid_header,
                                                         sms_campaign_of_current_user):
        """
        Trying to schedule a campaign with non int frequency Id, It should get bad request error,
        :return:
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = fake.word()
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_schedule_with_not_owned_campaign(self, valid_header,
                                                       sms_campaign_of_other_user):
        """
        Trying to schedule a campaign of some other user, It should get forbidden error,
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_other_user.id,
                                 headers=valid_header,
                                 data=json.dumps(generate_campaign_schedule_data()))
        assert response.status_code == ForbiddenError.http_status_code()

    def test_campaign_schedule_with_non_json_data_type(self, valid_header,
                                                       sms_campaign_of_current_user):
        """
        Trying to schedule a campaign of with Non JSON data, It should get bad request error,
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=generate_campaign_schedule_data())
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
                                 data=json.dumps(generate_campaign_schedule_data()))
        assert response.status_code == ResourceNotFound.http_status_code()

