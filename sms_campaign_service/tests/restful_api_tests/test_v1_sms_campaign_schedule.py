"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/schedule of SMS Campaign API.
"""
# Third Party Imports
import requests
import pytest

# Service Specific
from sms_campaign_service.common.models.misc import Frequency
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from sms_campaign_service.tests.modules.common_functions import generate_campaign_schedule_data


class TestSmsCampaignScheduleHTTPPOST(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns/:id/schedule.
    """
    HTTP_METHOD = 'post'
    URL = SmsCampaignApiUrl.SCHEDULE

    def test_campaign_schedule_with_valid_data(self, data_for_different_users_of_same_domain,
                                               sms_campaign_of_user_first, one_time_and_periodic):
        """
        Here we schedule a campaign, both one time and periodically. We shouldn't get any error.
        This runs for both users
        1) Who created the campaign and 2) Some other user of same domain
        """
        campaign = sms_campaign_of_user_first
        # Assert that initially campaign has no values saved related to scheduler.
        assert not campaign['frequency']
        assert not campaign['start_datetime']
        assert not campaign['end_datetime']
        task_id = CampaignsTestsHelpers.assert_campaign_schedule_or_reschedule(
            self.HTTP_METHOD, self.URL, data_for_different_users_of_same_domain['access_token'],
            data_for_different_users_of_same_domain['user'].id, campaign['id'],
            SmsCampaignApiUrl.CAMPAIGN, one_time_and_periodic)
        one_time_and_periodic['task_id'] = task_id

    def test_campaign_schedule_with_deleted_smartlist(self, access_token_first,
                                                      sms_campaign_of_user_first, one_time_and_periodic):
        """
        Here we schedule a campaign which is associated with a delete smartlist.
        On scheduling such campaign, API will raise InvalidUsage 400 error.
        """
        campaign = sms_campaign_of_user_first
        smartlist_id = campaign['smartlist_ids'][0]
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL % campaign['id'],
                                                                  access_token_first, smartlist_id,
                                                                  one_time_and_periodic,)

    def test_campaign_schedule_with_no_auth_header(self, access_token_first,
                                                   sms_campaign_of_user_first):
        """
        Using no Auth header like dict(Authorization='Bearer %s' % 'invalid_token'),
        just passing auth token as str. It should get Attribute Error.
        """
        try:
            requests.post(self.URL % sms_campaign_of_user_first['id'],
                          headers=access_token_first)
        except AttributeError as e:
            assert 'unicode' in e.message

    def test_campaign_schedule_with_invalid_token(self, sms_campaign_of_user_first):
        """
        User auth token is invalid. It should result in Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'],
            generate_campaign_schedule_data())

    def test_campaign_schedule_with_invalid_header(self, access_token_first,
                                                   sms_campaign_of_user_first):
        """
        Making POST call with no content-type specifying. It should result in bad request error.
        """
        response = requests.post(self.URL % sms_campaign_of_user_first['id'],
                                 headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaign_schedule_with_invalid_frequency_id(self, access_token_first, sms_campaign_of_user_first):
        """
        Trying to schedule a campaign with invalid frequency_id. It should get result in bad request error.
        """
        data = generate_campaign_schedule_data()
        CampaignsTestsHelpers.campaign_schedule_or_reschedule_with_invalid_frequency_id(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'], access_token_first, data)

    def test_campaign_schedule_with_not_owned_campaign(self, access_token_first,
                                                       sms_campaign_in_other_domain):
        """
        Trying to schedule a campaign of some other user, It should result in forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % sms_campaign_in_other_domain['id'],
                                                          access_token_first,
                                                          data=generate_campaign_schedule_data())

    def test_campaign_schedule_with_non_json_data_type(self, headers,
                                                       sms_campaign_of_user_first):
        """
        Trying to schedule a campaign of with Non JSON data, It should get result in request error.
        """
        response = requests.post(self.URL % sms_campaign_of_user_first['id'],
                                 headers=headers,
                                 data=generate_campaign_schedule_data())
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaign_schedule_with_no_data(self, headers, sms_campaign_of_user_first):
        """
        Trying to schedule a campaign of with no data, It should get result in request error.
        """
        response = requests.post(self.URL % sms_campaign_of_user_first['id'],
                                 headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaign_schedule_with_deleted_resource(self, access_token_first,
                                                     sms_campaign_of_user_first):
        """
        Here we first delete the campaign from database. Then we try to schedule it. It
        should result in ResourceNotFound error.
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_user_first,
                                                              SmsCampaignApiUrl.CAMPAIGN, self.URL, self.HTTP_METHOD,
                                                              access_token_first,
                                                              data=generate_campaign_schedule_data())

    def test_campaign_schedule_with_past_datetimes(self, sms_campaign_of_user_first,
                                                   access_token_first, one_time_and_periodic):
        """
        This is test to schedule SMS campaign with past start_datetime and end_datetime.
        It should get invalid usage error.
        """
        CampaignsTestsHelpers.request_with_past_start_and_end_datetime(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'], access_token_first,
            one_time_and_periodic)

    def test_campaign_schedule_with_missing_fields(self, access_token_first,
                                                   sms_campaign_of_user_first,
                                                   one_time_and_periodic):
        """
        This is the a to schedule a campaign with missing required fields.
        """
        CampaignsTestsHelpers.missing_fields_in_schedule_data(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'], access_token_first,
            one_time_and_periodic)

    def test_campaign_schedule_with_unexpected_field_in_data(self, access_token_first, sms_campaign_of_user_first):
        """
        This adds one unexpected field in data to schedule a campaign. It should result in Invalid usage error.
        """
        CampaignsTestsHelpers.test_api_with_with_unexpected_field_in_data(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'], access_token_first,
            generate_campaign_schedule_data())

    def test_campaign_schedule_with_invalid_datetime_format(self, access_token_first,
                                                            sms_campaign_of_user_first,
                                                            one_time_and_periodic):
        """
        This is the a to schedule a campaign with invalid datetime formats
        """
        CampaignsTestsHelpers.invalid_datetime_format(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'],
            access_token_first, one_time_and_periodic)

    def test_campaign_schedule_with_put_method(self, access_token_first,
                                               sms_campaign_of_user_first):
        """
        This test tries to schedule a campaign with PUT method. It should get forbidden error
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            'put', self.URL % sms_campaign_of_user_first['id'], access_token_first,
            data=generate_campaign_schedule_data())

    def test_schedule_campaign_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to schedule a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               generate_campaign_schedule_data())

    @pytest.mark.qa
    def test_schedule_campaign_with_start_time_greater_than_end_time(self, access_token_first,
                                                                     sms_campaign_of_user_first):
        """
        The test is to validate that, if start_datetime is greater than end_datetime then
        scheduler endpoint should throw invalid usage exception.
        """
        CampaignsTestsHelpers.start_time_greater_than_end_time(self.HTTP_METHOD,
                                                               self.URL % sms_campaign_of_user_first['id'],
                                                               access_token_first)


class TestSmsCampaignScheduleHTTPPUT(object):
    """
    This class contains tests for /v1/sms-campaigns/:id/schedule HTTP PUT method.
    """
    HTTP_METHOD = 'put'
    URL = SmsCampaignApiUrl.SCHEDULE

    def test_reschedule_campaign_from_one_time_to_periodic(self, access_token_first, user_first,
                                                           scheduled_sms_campaign_of_user_first):
        """
        Campaign is scheduled one time. Here we try to re-schedule it periodically with valid data.
        It should be re-scheduled.
        """
        campaign_id = scheduled_sms_campaign_of_user_first['id']
        data = generate_campaign_schedule_data()
        data['frequency_id'] = Frequency.DAILY  # for Periodic job
        CampaignsTestsHelpers.assert_campaign_schedule_or_reschedule(
            self.HTTP_METHOD, self.URL, access_token_first, user_first.id, campaign_id, SmsCampaignApiUrl.CAMPAIGN,
            data)

    def test_reschedule_campaign_with_other_user_of_same_domain(self, access_token_same, user_same_domain,
                                                                scheduled_sms_campaign_of_user_first):
        """
        Campaign is scheduled one time. Here we try to re-schedule it periodically with valid data
        with some other user of same domain. It should be re-scheduled.
        """
        campaign_id = scheduled_sms_campaign_of_user_first['id']
        data = generate_campaign_schedule_data()
        data['frequency_id'] = Frequency.DAILY  # for Periodic job
        CampaignsTestsHelpers.assert_campaign_schedule_or_reschedule(
            self.HTTP_METHOD, self.URL, access_token_same, user_same_domain.id, campaign_id, SmsCampaignApiUrl.CAMPAIGN,
            data)

    def test_reschedule_campaign_with_invalid_token(self, sms_campaign_of_user_first):
        """
        Auth token is invalid. It should get Un-authorized error
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL
                                                         % sms_campaign_of_user_first['id'],
                                                         generate_campaign_schedule_data())

    def test_reschedule_campaign_with_invalid_data(self, access_token_first,
                                                   scheduled_sms_campaign_of_user_first):
        """
        This is the test for PUT endpoint with invalid data e.g. empty dict, None data etc.
        """
        CampaignsTestsHelpers.reschedule_with_invalid_data(
            self.URL % scheduled_sms_campaign_of_user_first['id'], access_token_first)

    def test_reschedule_campaign_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               generate_campaign_schedule_data()
                                                               )

    def test_reschedule_campaign_with_post_method(self, access_token_first,
                                                  scheduled_sms_campaign_of_user_first):
        """
        To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        """
        CampaignsTestsHelpers.reschedule_with_post_method(
            self.URL % scheduled_sms_campaign_of_user_first['id'], access_token_first,
            generate_campaign_schedule_data())

    def test_campaign_reschedule_with_missing_fields_in_data(
            self, access_token_first, scheduled_sms_campaign_of_user_first,
            one_time_and_periodic):
        """
        Here we try to reschedule given campaign periodically an one time. And test by no
        start_datetime and no end_datetime. It should get Invalid usage error.
        """
        CampaignsTestsHelpers.missing_fields_in_schedule_data(
            self.HTTP_METHOD, self.URL % scheduled_sms_campaign_of_user_first['id'],
            access_token_first, one_time_and_periodic)

    def test_campaign_reschedule_with_unexpected_field_in_data(self, access_token_first,
                                                               scheduled_sms_campaign_of_user_first):
        """
        This adds one unexpected field in data to reschedule a campaign. It should result in Invalid usage error.
        """
        CampaignsTestsHelpers.test_api_with_with_unexpected_field_in_data(
            self.HTTP_METHOD, self.URL % scheduled_sms_campaign_of_user_first['id'], access_token_first,
            generate_campaign_schedule_data())

    def test_reschedule_campaign_with_invalid_datetime_format(
            self, access_token_first, scheduled_sms_campaign_of_user_first,
            one_time_and_periodic):
        """
        Campaign is scheduled one time. Here we try to re-schedule it periodically and one_time.
        We pass datetime with invalid format. We then assert that we get Invalid usage error.
        """
        CampaignsTestsHelpers.invalid_datetime_format(
            self.HTTP_METHOD, self.URL % scheduled_sms_campaign_of_user_first['id'],
            access_token_first, one_time_and_periodic)

    def test_reschedule_not_owned_campaign(self, access_token_first,
                                           scheduled_sms_campaign_of_other_domain):
        """
        Trying to re-schedule a campaign of some other user, It should get forbidden error,
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % scheduled_sms_campaign_of_other_domain['id'],
            access_token_first, data=generate_campaign_schedule_data())

    def test_reschedule_deleted_campaign(self, access_token_first, scheduled_sms_campaign_of_user_first):
        """
        Here we first delete the campaign from database. Then we try to re-schedule it. It
        should result in ResourceNotFound error.
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(scheduled_sms_campaign_of_user_first,
                                                              SmsCampaignApiUrl.CAMPAIGN, self.URL, self.HTTP_METHOD,
                                                              access_token_first,
                                                              data=generate_campaign_schedule_data())

    def test_campaign_reschedule_with_deleted_smartlist(self, access_token_first, scheduled_sms_campaign_of_user_first,
                                               sms_campaign_of_user_first, one_time_and_periodic):
        """
        Here we reschedule a campaign which is associated with a delete smartlist.
        On rescheduling such campaign, API will raise InvalidUsage 400 error.
        """
        campaign = sms_campaign_of_user_first
        campaign_id = campaign['id']
        smartlist_id = sms_campaign_of_user_first['smartlist_ids'][0]
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL % campaign_id,
                                                                  access_token_first, smartlist_id,
                                                                  one_time_and_periodic)

    def test_reschedule_campaign_with_invalid_frequency_id(self, access_token_first,
                                                           scheduled_sms_campaign_of_user_first):
        """
        Trying to re-schedule a campaign with invalid frequency_id, It should result in bad request error.
        """
        data = generate_campaign_schedule_data()
        CampaignsTestsHelpers.campaign_schedule_or_reschedule_with_invalid_frequency_id(
            self.HTTP_METHOD, self.URL % scheduled_sms_campaign_of_user_first['id'], access_token_first, data)

    @pytest.mark.qa
    def test_reschedule_campaign_with_start_time_greater_than_end_time(self, access_token_first,
                                                                       scheduled_sms_campaign_of_user_first):
        """
        Reschedule a campaign with start_time greater than end_time.
        Api should raise InvalidUsage error 400
        """
        CampaignsTestsHelpers.start_time_greater_than_end_time(self.HTTP_METHOD,
                                                               self.URL % scheduled_sms_campaign_of_user_first['id'],
                                                               access_token_first)


class TestSmsCampaignScheduleHTTPDELETE(object):
    """
    This class contains tests for /v1/sms-campaigns/:id/schedule HTTP DELETE method.
    """
    HTTP_METHOD = 'delete'
    URL = SmsCampaignApiUrl.SCHEDULE

    def test_unschedule_campaign_with_invalid_token(self, sms_campaign_of_user_first):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'],
            generate_campaign_schedule_data())

    def test_unschedule_campaign_with_invalid_campaign_id(self, access_token_first):
        """
        Test with invalid integer id
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(
            SmsCampaign, self.HTTP_METHOD, self.URL, access_token_first,
            generate_campaign_schedule_data())

    def test_unschedule_a_campaign(self, data_for_different_users_of_same_domain,
                                   scheduled_sms_campaign_of_user_first):
        """
        Here we un schedule a campaign. It should get OK response.

        This runs for both users
        1) Who created the campaign and 2) Some other user of same domain
        """
        # It should get campaign has been un scheduled
        response = requests.delete(
            self.URL % scheduled_sms_campaign_of_user_first['id'],
            headers=data_for_different_users_of_same_domain['headers'])
        assert response.ok
        # It should get campaign is already unscheduled
        response = requests.delete(
            self.URL % scheduled_sms_campaign_of_user_first['id'],
            headers=data_for_different_users_of_same_domain['headers'])
        assert response.ok

    def test_unschedule_not_owned_campaign(self, access_token_first,
                                           scheduled_sms_campaign_of_other_domain):
        """
        Here we try to un schedule a campaign of some other user. It should get forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % scheduled_sms_campaign_of_other_domain['id'],
            access_token_first)

    def test_unschedule_with_deleted_resource(self, access_token_first,
                                              scheduled_sms_campaign_of_user_first):
        """
        Here we first delete the campaign from database. Then we try to unschedule it. It
        should result in ResourceNotFound error,
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(
            scheduled_sms_campaign_of_user_first,
            SmsCampaignApiUrl.CAMPAIGN,
            self.URL,
            self.HTTP_METHOD,
            access_token_first)
