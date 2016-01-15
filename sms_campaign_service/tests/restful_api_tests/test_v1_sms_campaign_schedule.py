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
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.common.tests.auth_utilities import to_utc_str
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.common.campaign_services.campaign_utils import FrequencyIds
from sms_campaign_service.tests.modules.common_functions import (assert_method_not_allowed,
                                                                 assert_campaign_delete)
from sms_campaign_service.common.campaign_services.common_tests import CampaignsCommonTests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl, SmsCampaignApi
from sms_campaign_service.common.error_handling import (UnauthorizedError, InvalidUsage,
                                                        ForbiddenError,
                                                        ResourceNotFound)


class TestSmsCampaignScheduleHTTPPOST(object):
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

    def test_campaign_schedule_with_deleted_resource(self, valid_header, sample_user,
                                                     sms_campaign_of_current_user):
        """
        Here we first delete the campaign from database. Then we try to schedule it. It
        should get ResourceNotFound error,
        """
        campaign_id = sms_campaign_of_current_user.id
        # Delete the campaign first
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % campaign_id,
                                   headers=valid_header)
        assert_campaign_delete(response, sample_user.id, campaign_id)
        # Try to schedule deleted campaign
        response = requests.post(SmsCampaignApiUrl.SCHEDULE % campaign_id,
                                 headers=valid_header,
                                 data=json.dumps(generate_campaign_schedule_data()))
        assert response.status_code == ResourceNotFound.http_status_code()

    def test_campaign_periodic_schedule_with_past_end_date(
            self, valid_header, sample_user, sms_campaign_of_current_user,
            sms_campaign_smartlist, sample_sms_campaign_candidates, candidate_phone_1):
        """
        This is test to schedule SMS campaign with all valid parameters. This should get OK
         response
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = FrequencyIds.DAILY  # for Periodic job
        data['end_datetime'] = to_utc_str(datetime.utcnow() - timedelta(hours=10))
        response = requests.post(
            SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
            headers=valid_header, data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_periodic_schedule_with_missing_fields(self, auth_token,
                                                            sms_campaign_of_current_user):
        data = generate_campaign_schedule_data()
        data['frequency_id'] = FrequencyIds.DAILY  # for Periodic job
        CampaignsCommonTests.missing_fields_in_schedule_data('post',
                                                             SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
                                                             auth_token, data)

    def test_campaign_periodic_schedule_with_invalid_datetime_format(self, auth_token,
                                                                     sms_campaign_of_current_user):
        data = generate_campaign_schedule_data()
        data['frequency_id'] = FrequencyIds.DAILY  # for Periodic job
        CampaignsCommonTests.invalid_datetime_format(
            SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id, auth_token, data)


class TestSmsCampaignScheduleHTTPPUT(object):
    """
    This class contains tests for /v1/campaigns/:id/schedule HTTP PUT method.
    """

    def test_schedule_campaign_with_put_method(self, auth_token, sms_campaign_of_current_user):
        """
        This test tries to schedule a campaign with PUT method. It should get forbidden error
        :return:
        """
        CampaignsCommonTests.schedule_with_put_method(
            SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id, auth_token,
            generate_campaign_schedule_data())

    def test_reschedule_campaign_with_invalid_token(self, sms_campaign_of_current_user):
        """
        Auth token is invalid. It should get Un-authorized error
        :param sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.reschedule_with_invalid_token(SmsCampaignApiUrl.SCHEDULE
                                                           % sms_campaign_of_current_user.id,
                                                           generate_campaign_schedule_data())

    def test_reschedule_campaign_with_invalid_data(self, auth_token,
                                                   scheduled_sms_campaign_of_current_user):
        """
        This is the test for PUT endpoint with invalid data
        :return:
        """
        CampaignsCommonTests.reschedule_with_invalid_data(
            SmsCampaignApiUrl.SCHEDULE % scheduled_sms_campaign_of_current_user.id, auth_token)

    def test_reschedule_campaign_with_invalid_campaign_id(self, auth_token):
        """
        This is a test to update a campaign which does not exists in database.
        :param auth_token:
        :return:
        """
        last_campaign_id_in_db = SmsCampaign.query.order_by(SmsCampaign.id.desc()).first().id
        CampaignsCommonTests.reschedule_with_invalid_campaign_id(SmsCampaignApiUrl.SCHEDULE,
                                                                 auth_token,
                                                                 generate_campaign_schedule_data(),
                                                                 last_campaign_id_in_db)

    def test_reschedule_campaign_with_post_method(self, auth_token,
                                                  scheduled_sms_campaign_of_current_user):
        """
        To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        :param auth_token:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.reschedule_with_post_method(
            SmsCampaignApiUrl.SCHEDULE % scheduled_sms_campaign_of_current_user.id, auth_token,
            generate_campaign_schedule_data())

    def test_campaign_periodic_reschedule_with_missing_fields_in_data(
            self, auth_token, scheduled_sms_campaign_of_current_user):
        """
        Here we try to reschedule given campaign periodically. And test by no start_datetime
        and no end_datetime. It should get Invalid usage error.
        :param auth_token:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = FrequencyIds.DAILY  # for Periodic job
        CampaignsCommonTests.missing_fields_in_schedule_data(
            'put', SmsCampaignApiUrl.SCHEDULE % scheduled_sms_campaign_of_current_user.id,
            auth_token, data, one_time_job=False)

    def test_campaign_one_time_reschedule_with_missing_fields_in_data(
            self, auth_token, scheduled_sms_campaign_of_current_user):
        """
        Here we try to reschedule given campaign one time. And test by no start_datetime.
        It should get Invalid usage error.
        :param auth_token:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.missing_fields_in_schedule_data(
            'put', SmsCampaignApiUrl.SCHEDULE % scheduled_sms_campaign_of_current_user.id,
            auth_token, generate_campaign_schedule_data())
