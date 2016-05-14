"""
This module contains test for API endpoint
        /v1/push-campaigns/:id/schedule

In these tests, we will try to get a campaign's sends
in different scenarios like:

Schedule a campaign: /v1/push-campaigns/:id/schedule [POST]
    - with invalid token
    - with invalid data (empty data, invalid data, with json headers)
    - with non existing campaign
    - with PUT method (400)
    - With missing required fields in schedule data
    - with invalid datetime format in schedule data
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
    - with valid token and valid schedule data (200)

Reschedule a campaign: /v1/push-campaigns/:id/schedule [PUT]
    - with invalid token
    - with invalid data (empty data, invalid data, with json headers)
    - with non existing campaign
    - with POST method (400)
    - With missing required fields in schedule data
    - with invalid datetime format in schedule data
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
    - with valid token and valid schedule data (200)

Unschedule a campaign: /v1/push-campaigns/:id/schedule [DELETE]
    - with invalid token
    - with non existing campaign
    - where campaign is created by user from different domain (403)
    - where campaign is created by different user from same domain (200)
    - with valid token (200)
"""
# Builtin imports
import sys
from datetime import datetime

# 3rd party imports
from redo import retry
from requests import codes

# Application specific imports
from push_campaign_service.tests.test_utilities import (generate_campaign_schedule_data,
                                                        schedule_campaign, invalid_data_test,
                                                        reschedule_campaign, unschedule_campaign, get_blasts)
from push_campaign_service.common.utils.test_utils import send_request
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test
from push_campaign_service.common.models.misc import Frequency

URL = PushCampaignApiUrl.SCHEDULE


class TestScheduleCampaignUsingPOST(object):

    # Test URL: /v1/push-campaigns/{id}/schedule [POST]
    def test_schedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        """
        Try to schedule a campaign with invalid AuthToken and API will rasie Unauthorized error (401).
        """
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        campaign_id = campaign_in_db['id']
        schedule_campaign(campaign_id, data, 'invalid_token', expected_status=(codes.UNAUTHORIZED,))

    def test_schedule_campaign_with_invalid_data(self, token_first, campaign_in_db, smartlist_first):
        """
        Schedule a campaign with invalid data and API will  raise InvalidUsage.
        """
        invalid_data_test('post', URL % campaign_in_db['id'], token_first)

    def test_schedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db, smartlist_first):
        """
        Try to schedule a campaign that does not exists, it will raise BadRequest (400 in case of 0) or NotFound 404.
        """
        data = generate_campaign_schedule_data()
        # Test with invalid or non-existing id
        non_existing_id = sys.maxint
        invalid_ids = [(0, codes.BAD_REQUEST),
                       (non_existing_id, codes.NOT_FOUND)]
        for _id, status_code in invalid_ids:
            schedule_campaign(_id, data, token_first, expected_status=(status_code,))

    def test_schedule_campaign_with_put_method(self, token_first, campaign_in_db, smartlist_first):
        """
        Test forbidden error. To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        """
        data = generate_campaign_schedule_data()
        reschedule_campaign(campaign_in_db['id'], data, token_first,
                            expected_status=(codes.FORBIDDEN,))

    def test_schedule_campaign_with_missing_fields_in_schedule_data(self, token_first, campaign_in_db,
                                                           smartlist_first):
        """
        Schedule a campaign without `start_datetime` in schedule data and it will raise InvalidUsage (400).
        """
        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['start_datetime']
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(codes.BAD_REQUEST,))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['end_datetime']
        response = schedule_campaign(campaign_in_db['id'], data, token_first,
                                     expected_status=(codes.BAD_REQUEST,))
        error = response['error']
        assert 'end_datetime' in error['message']

    def test_schedule_compaign_with_invalid_datetime_format(self, token_first, campaign_in_db,
                                                           smartlist_first):
        """
        In this test, we will schedule a campaign with invalid datetime format and  it will raise an error 400.
        """
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        start = datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(codes.BAD_REQUEST,))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        end = datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(codes.BAD_REQUEST,))

    def test_schedule_a_campaign_with_valid_data(self, smartlist_first, campaign_in_db, talent_pool,
                                                 token_first, candidate_device_first):
        """
        In this test, we will schedule a campaign with all valid data and it should return an OK response and campaign
        should be scheduled.
        """
        data = generate_campaign_schedule_data()
        response = schedule_campaign(campaign_in_db['id'], data, token_first, expected_status=(codes.OK,))
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        # retry(get_blasts, sleeptime=3, attempts=20, sleepscale=1, retry_exceptions=(AssertionError,),
        #       args=(campaign_in_db['id'], token_first), kwargs={'count': 1})

    def test_schedule_a_campaign_with_user_from_same_domain(self, smartlist_first, campaign_in_db,  talent_pool,
                                                            token_first, token_same_domain,  candidate_device_first):
        """
        In this test, we will schedule a campaign using different user's auth token, but user is from same domain ,
        as the actual owner of the campaign. So we are expecting that , response will be OK and campaign will be
        scheduled.
        """

        campaign_id = campaign_in_db['id']
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        response = schedule_campaign(campaign_id, data, token_same_domain, expected_status=(codes.OK,))
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        # retry(get_blasts, attempts=20, sleepscale=1, retry_exceptions=(AssertionError,),
        #       args=(campaign_id, token_first), kwargs={'count': 1})

    def test_schedule_a_campaign_with_user_from_diff_domain(self, token_first, token_second,
                                                            campaign_in_db, smartlist_first, candidate_device_first):
        """
        Test with a valid campaign but user is not owner of campaign
        Here we created campaign with user whose Auth token_first is "token_first"
        and we want to schedule this campaign with other user with token_first "token_second"
        :param token_second: auth token for user from different domain
        :param token_first: auth token for first user
        :param campaign_in_db: campaign dict object
        """
        data = generate_campaign_schedule_data()
        schedule_campaign(campaign_in_db['id'], data, token_second, expected_status=(codes.FORBIDDEN,))


class TestRescheduleCampaignUsingPUT(object):

    # Test URL: /v1/push-campaigns/{id}/schedule [PUT]
    def test_reschedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        """
        Try to reschedule a campaign with invalid AuthToken and API will raise Unauthorized error (401).
        """
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        campaign_id = campaign_in_db['id']
        reschedule_campaign(campaign_id, data, 'invalid_token', expected_status=(codes.UNAUTHORIZED,))

    def test_reschedule_campaign_with_other_user(self, token_second, campaign_in_db):
        """
        Test with a valid campaign but user is not owner of campaign
        Here we created campaign with user whose Auth token_first is "token_first"
        and we want to reschedule this campaign using different token_first "token_second"
        """
        data = generate_campaign_schedule_data()
        reschedule_campaign(campaign_in_db['id'], data, token_second,
                            expected_status=(codes.FORBIDDEN,))

    def test_reschedule_campaign_with_invalid_data(self, token_first, campaign_in_db, smartlist_first):
        """
        Reschedule a campaign with invalid data and API will  raise InvalidUsage.
        """
        invalid_data_test('put', URL % campaign_in_db['id'], token_first)

    def test_reschedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db,
                                                          smartlist_first,
                                                          schedule_a_campaign):
        """
        Try to reschedule a campaign that does not exists, it will raise BadRequest (for 0as id) or NotFoundError
        """
        data = generate_campaign_schedule_data()

        # Test with invalid integer id
        # Test for 404, Schedule a campaign which does not exists or id is invalid
        non_existing_id = sys.maxint
        invalid_ids = [(0, codes.BAD_REQUEST),
                       (non_existing_id, codes.NOT_FOUND)]
        for _id, status_code in invalid_ids:
            reschedule_campaign(_id, data, token_first, expected_status=(status_code,))

    def test_reschedule_campaign_with_post_method(self, token_first, campaign_in_db, smartlist_first,
                                                  schedule_a_campaign):
        """
        Test forbidden error. To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        """
        data = schedule_a_campaign
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(codes.FORBIDDEN,))

    def test_reschedule_campaign_with_missing_fields_in_schedule_data(self, token_first, campaign_in_db,
                                                           smartlist_first, schedule_a_campaign):
        """
        Reschedule a campaign without `start_datetime` or `end_datetime` in schedule data
        and it will raise InvalidUsage/BadRequest (400).
        """
        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['start_datetime']
        response = reschedule_campaign(campaign_in_db['id'], data, token_first,
                                       expected_status=(codes.BAD_REQUEST,))
        error = response['error']
        assert 'start_datetime' in error['message']

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['end_datetime']
        response = reschedule_campaign(campaign_in_db['id'], data, token_first,
                                       expected_status=(codes.BAD_REQUEST,))
        error = response['error']
        assert 'end_datetime' in error['message']

    def test_reschedule_campaign_with_invalid_datetime_format(self, token_first, campaign_in_db,
                                                            smartlist_first, schedule_a_campaign):
        """
        In this test, we will reschedule a campaign with invalid datetime format and  it will raise an error 400.
        """
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        start = datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        reschedule_campaign(campaign_in_db['id'], data, token_first,
                            expected_status=(codes.BAD_REQUEST,))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        end = datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        reschedule_campaign(campaign_in_db['id'], data, token_first,
                            expected_status=(codes.BAD_REQUEST,))

    def test_reschedule_campaign_with_valid_data(self, token_first, campaign_in_db, talent_pool, candidate_first,
                                             smartlist_first, schedule_a_campaign, candidate_device_first):
        """
        Reschedule a campaign with valid data and it should return 200 response.
        """

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        response = send_request('put', PushCampaignApiUrl.SCHEDULE % campaign_in_db['id'], token_first, data)
        assert response.status_code == codes.OK
        response = response.json()
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        # retry(get_blasts, attempts=20, sleepscale=1, sleeptime=3, retry_exceptions=(AssertionError,),
        #       args=(campaign_in_db['id'], token_first), kwargs={'count': 2})

    def test_reschedule_a_campaign_with_user_from_same_domain(self, token_first, token_same_domain,
                                                            campaign_in_db, schedule_a_campaign):
        """
        In this test, we will reschedule a campaign using different user's auth token, but user is from same domain ,
        as the actual owner of the campaign. So we are expecting that , response will be OK and campaign will be
        rescheduled.
        """
        data = generate_campaign_schedule_data()
        reschedule_campaign(campaign_in_db['id'], data, token_same_domain,
                            expected_status=(codes.FORBIDDEN,))


class TestUnscheduleCamapignUsingDELETE(object):

    # Test URL: /v1/push-campaigns/{id}/schedule [DELETE]
    def test_unschedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        """
         Try to unschedule a campaign with invalid aut token nd  API will raise 401 error.
        """
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('delete',  URL % campaign_in_db['id'], data)

    def test_unschedule_campaign_with_other_user(self, token_second, campaign_in_db):
        """
        Try to  unschedule a campaign with user auth token from different domain and it should
        raise Forbidden (403) error.
        """
        # Test with a valid campaign but user is not owner of campaign
        # Here we created campaign with user whose Auth token_first is "token_first"
        # and we have a a test user token_first "test_auth_token" to test ownership
        unschedule_campaign(campaign_in_db['id'], token_second, expected_status=(codes.FORBIDDEN,))

    def test_unschedule_campaign_with_other_user_but_same_domain(self, token_same_domain,
                                                                 campaign_in_db):
        """
        Test with a valid campaign and user is not owner of campaign but from same domain
        This user should be allowed to unschedule the campaign
        Here we created campaign with user whose Auth token_first is "token_first"
        """
        unschedule_campaign(campaign_in_db['id'], token_same_domain, expected_status=(codes.OK,))

    def test_unschedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db):
        """
        Try to unschedule a campaign that does not exists, it will raise BadRequest (400 in case of 0) or NotFound 404.
        """
        # Test with invalid integer id
        non_existing_id = sys.maxint
        invalid_ids = [(0, codes.BAD_REQUEST),
                       (non_existing_id, codes.NOT_FOUND)]
        for _id, status_code in invalid_ids:
            unschedule_campaign(_id, token_first, expected_status=(status_code,))

    def test_unschedule_a_campaign(self, token_first, campaign_in_db, smartlist_first,
                                   schedule_a_campaign):
        """
        Try to unschedule a scheduled campaign and it should be unscheduled successfully
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist for user_first
        :param schedule_a_campaign: a fixture to schedule a campaign
        """
        unschedule_campaign(campaign_in_db['id'], token_first, expected_status=(codes.OK,))


