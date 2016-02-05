"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/schedule of SMS Campaign API.
"""
# Standard Imports
import json

# Third Party Imports
import requests

# Service Specific
from sms_campaign_service.common.models.misc import Frequency
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.common.campaign_services.common_tests import CampaignsCommonTests


class TestSmsCampaignScheduleHTTPPOST(object):
    """
    This class contains tests for endpoint /v1/campaigns/:id/schedule.
    """
    METHOD = 'post'
    URL = SmsCampaignApiUrl.SCHEDULE

    def test_campaign_schedule_with_valid_data(self, access_token_first,
                                               sms_campaign_of_current_user,
                                               one_time_and_periodic):
        """
        Here we reschedule a campaign, both one time and periodically. We shouldn't get
        any error.
        """
        task_id = CampaignsCommonTests.request_for_ok_response(
            self.METHOD, self.URL % sms_campaign_of_current_user.id,
            access_token_first, one_time_and_periodic)
        one_time_and_periodic['task_id'] = task_id

    def test_campaign_schedule_with_no_auth_header(self, access_token_first, sms_campaign_of_current_user):
        """
        Using no Auth header like dict(Authorization='Bearer %s' % 'invalid_token'),
        just passing auth token as str. It should get Attribute Error.
        :return:
        """
        try:
            requests.post(self.URL % sms_campaign_of_current_user.id,
                          headers=access_token_first)
        except AttributeError as e:
            assert 'unicode' in e.message

    def test_campaign_schedule_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        CampaignsCommonTests.request_with_invalid_token(
            self.METHOD, self.URL % sms_campaign_of_current_user.id,
            generate_campaign_schedule_data())

    def test_campaign_schedule_with_invalid_header(self, access_token_first, sms_campaign_of_current_user):
        """
        Making POST call with no content-type specifying. It should get bad request error.
        :return:
        """
        response = requests.post(self.URL % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsCommonTests.assert_api_response(response)

    def test_campaign_schedule_with_non_existing_frequency_id(self, valid_header,
                                                              sms_campaign_of_current_user):
        """
        Trying to schedule a campaign with invalid frequency Id, Valid ids are in [1,2,3..6] for
        now. It should get bad request error.
        :return:
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = fake.numerify()  # this returns a three digit random number
        response = requests.post(self.URL % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        CampaignsCommonTests.assert_api_response(response)

    def test_campaign_schedule_with_invalid_frequency_id(self, valid_header,
                                                         sms_campaign_of_current_user):
        """
        Trying to schedule a campaign with non int frequency Id, It should get bad request error,
        :return:
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = fake.word()
        response = requests.post(self.URL % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=json.dumps(data))
        CampaignsCommonTests.assert_api_response(response)

    def test_campaign_schedule_with_not_owned_campaign(self, access_token_first,
                                                       sms_campaign_of_other_user):
        """
        Trying to schedule a campaign of some other user, It should get forbidden error,
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(self.METHOD,
                                                         self.URL % sms_campaign_of_other_user.id,
                                                         access_token_first)

    def test_campaign_schedule_with_non_json_data_type(self, valid_header,
                                                       sms_campaign_of_current_user):
        """
        Trying to schedule a campaign of with Non JSON data, It should get bad request error,
        :return:
        """
        response = requests.post(self.URL % sms_campaign_of_current_user.id,
                                 headers=valid_header,
                                 data=generate_campaign_schedule_data())
        CampaignsCommonTests.assert_api_response(response)

    def test_campaign_schedule_with_no_data(self, valid_header, sms_campaign_of_current_user):
        """
        Trying to schedule a campaign of with no data, It should get bad request error,
        :return:
        """
        response = requests.post(self.URL % sms_campaign_of_current_user.id,
                                 headers=valid_header)
        CampaignsCommonTests.assert_api_response(response)

    def test_campaign_schedule_with_deleted_resource(self, access_token_first,
                                                     sms_campaign_of_current_user):
        """
        Here we first delete the campaign from database. Then we try to schedule it. It
        should get ResourceNotFound error,
        """
        CampaignsCommonTests.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                             SmsCampaignApiUrl.CAMPAIGN,
                                                             self.URL,
                                                             self.METHOD,
                                                             access_token_first)

    def test_campaign_one_time_schedule_with_past_datetimes(self, sms_campaign_of_current_user,
                                                            access_token_first, one_time_and_periodic):
        """
        This is test to schedule SMS campaign with past start_datetime and end_datetime.
        It should get invalid usage error.
        """
        CampaignsCommonTests.request_with_past_start_and_end_datetime(
            self.METHOD, self.URL % sms_campaign_of_current_user.id, access_token_first,
            one_time_and_periodic)

    def test_campaign_schedule_with_missing_fields(self, access_token_first,
                                                   sms_campaign_of_current_user,
                                                   one_time_and_periodic):
        """
        This is the a to schedule a campaign with missing required fields.
        """
        CampaignsCommonTests.missing_fields_in_schedule_data(
            self.METHOD, self.URL % sms_campaign_of_current_user.id, access_token_first,
            one_time_and_periodic)

    def test_campaign_schedule_with_invalid_datetime_format(self, access_token_first,
                                                            sms_campaign_of_current_user,
                                                            one_time_and_periodic):
        """
        This is the a to schedule a campaign with invalid datetime formats
        """
        CampaignsCommonTests.invalid_datetime_format(
            self.METHOD, self.URL % sms_campaign_of_current_user.id,
            access_token_first, one_time_and_periodic)

    def test_schedule_campaign_with_put_method(self, access_token_first, sms_campaign_of_current_user):
        """
        This test tries to schedule a campaign with PUT method. It should get forbidden error
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(
            'put', self.URL % sms_campaign_of_current_user.id, access_token_first)

    def test_schedule_campaign_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to schedule a campaign which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsCommonTests.request_with_invalid_campaign_id(SmsCampaign,
                                                              self.METHOD,
                                                              self.URL,
                                                              access_token_first,
                                                              generate_campaign_schedule_data())


class TestSmsCampaignScheduleHTTPPUT(object):
    """
    This class contains tests for /v1/campaigns/:id/schedule HTTP PUT method.
    """
    METHOD = 'put'
    URL = SmsCampaignApiUrl.SCHEDULE

    def test_reschedule_campaign_from_one_time_to_periodic(
            self, access_token_first, scheduled_sms_campaign_of_current_user):
        """
        Campaign is scheduled one time. Here we try to re-schedule it periodically with valid data.
        It should be re-scheduled.
        :param access_token_first:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = Frequency.DAILY  # for Periodic job
        CampaignsCommonTests.request_for_ok_response(
            self.METHOD, self.URL % scheduled_sms_campaign_of_current_user.id,
            access_token_first, data)

    def test_reschedule_campaign_with_invalid_token(self, sms_campaign_of_current_user):
        """
        Auth token is invalid. It should get Un-authorized error
        :param sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.request_with_invalid_token(self.METHOD, self.URL
                                                        % sms_campaign_of_current_user.id,
                                                        generate_campaign_schedule_data())

    def test_reschedule_campaign_with_invalid_data(self, access_token_first,
                                                   scheduled_sms_campaign_of_current_user):
        """
        This is the test for PUT endpoint with invalid data e.g. empty dict, None data etc.
        :return:
        """
        CampaignsCommonTests.reschedule_with_invalid_data(
            self.URL % scheduled_sms_campaign_of_current_user.id, access_token_first)

    def test_reschedule_campaign_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsCommonTests.request_with_invalid_campaign_id(SmsCampaign,
                                                              self.METHOD,
                                                              self.URL,
                                                              access_token_first,
                                                              generate_campaign_schedule_data()
                                                              )

    def test_reschedule_campaign_with_post_method(self, access_token_first,
                                                  scheduled_sms_campaign_of_current_user):
        """
        To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        :param access_token_first:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.reschedule_with_post_method(
            self.URL % scheduled_sms_campaign_of_current_user.id, access_token_first,
            generate_campaign_schedule_data())

    def test_campaign_reschedule_with_missing_fields_in_data(
            self, access_token_first, scheduled_sms_campaign_of_current_user, one_time_and_periodic):
        """
        Here we try to reschedule given campaign periodically an one time. And test by no
        start_datetime and no end_datetime. It should get Invalid usage error.
        :param access_token_first:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.missing_fields_in_schedule_data(
            self.METHOD, self.URL % scheduled_sms_campaign_of_current_user.id,
            access_token_first, one_time_and_periodic)

    def test_reschedule_campaign_with_invalid_datetime_format(
            self, access_token_first, scheduled_sms_campaign_of_current_user, one_time_and_periodic):
        """
        Campaign is scheduled one time. Here we try to re-schedule it periodically and one_time.
        We pass datetime with invalid format. We then assert that we get Invalid usage error.
        :param access_token_first:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        CampaignsCommonTests.invalid_datetime_format(
            self.METHOD, self.URL % scheduled_sms_campaign_of_current_user.id,
            access_token_first, one_time_and_periodic)

    def test_reschedule_not_owned_campaign(self, access_token_first,
                                           scheduled_sms_campaign_of_other_user):
        """
        Trying to re-schedule a campaign of some other user, It should get forbidden error,
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(
            self.METHOD, self.URL % scheduled_sms_campaign_of_other_user.id,
            access_token_first)

    def test_rescheduling_deleted_campaign(self, access_token_first,
                                           scheduled_sms_campaign_of_current_user):
        """
        Here we first delete the campaign from database. Then we try to re-schedule it. It
        should get ResourceNotFound error.
        """
        CampaignsCommonTests.request_after_deleting_campaign(scheduled_sms_campaign_of_current_user,
                                                             SmsCampaignApiUrl.CAMPAIGN,
                                                             self.URL,
                                                             self.METHOD,
                                                             access_token_first)


class TestSmsCampaignScheduleHTTPDELETE(object):
    """
    This class contains tests for /v1/campaigns/:id/schedule HTTP DELETE method.
    """
    METHOD = 'delete'
    URL = SmsCampaignApiUrl.SCHEDULE

    def test_unschedule_campaign_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        CampaignsCommonTests.request_with_invalid_token(
            self.METHOD, self.URL % sms_campaign_of_current_user.id,
            generate_campaign_schedule_data())

    def test_unschedule_campaign_with_invalid_campaign_id(self, access_token_first):
        # Test with invalid integer id
        CampaignsCommonTests.request_with_invalid_campaign_id(
            SmsCampaign, self.METHOD, self.URL, access_token_first, generate_campaign_schedule_data())

    def test_unschedule_a_campaign(self, access_token_first, scheduled_sms_campaign_of_current_user):
        """
        Here we un schedule a campaign. It should get OK response.
        :param access_token_first:
        :param scheduled_sms_campaign_of_current_user:
        :return:
        """
        # It should get campaign has been un scheduled
        CampaignsCommonTests.request_for_ok_response(
            self.METHOD, self.URL % scheduled_sms_campaign_of_current_user.id,
            access_token_first, None)
        # It should get campaign is already unscheduled
        CampaignsCommonTests.request_for_ok_response(
            self.METHOD, self.URL % scheduled_sms_campaign_of_current_user.id,
            access_token_first, None)

    def test_unschedule_not_owned_campaign(self, access_token_first,
                                           scheduled_sms_campaign_of_other_user):
        """
        Here we try to un schedule a campaign of some other user. It should get forbidden error.
        :return:
        """
        CampaignsCommonTests.request_for_forbidden_error(
            self.METHOD, self.URL % scheduled_sms_campaign_of_other_user.id,
            access_token_first)

    def test_unschedule_with_deleted_resource(self, access_token_first,
                                              scheduled_sms_campaign_of_current_user):
        """
        Here we first delete the campaign from database. Then we try to unschedule it. It
        should get ResourceNotFound error,
        """
        CampaignsCommonTests.request_after_deleting_campaign(scheduled_sms_campaign_of_current_user,
                                                             SmsCampaignApiUrl.CAMPAIGN,
                                                             self.URL,
                                                             self.METHOD,
                                                             access_token_first)
