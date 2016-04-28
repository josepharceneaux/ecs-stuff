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
import time
from datetime import datetime
# 3rd party imports
from redo import retry
from requests import codes as HttpStatus
# Application specific imports
from push_campaign_service.tests.test_utilities import (generate_campaign_schedule_data,
                                                        schedule_campaign, invalid_data_test,
                                                        reschedule_campaign, get_blasts, SLEEP_TIME,
                                                        unschedule_campaign, get_campaigns, create_campaign)
from push_campaign_service.common.utils.test_utils import delete_scheduler_task, create_talent_pipelines, \
    create_candidate, get_candidate, create_smartlist, send_request, get_smartlist_candidates
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test
from push_campaign_service.common.models.misc import Frequency

URL = PushCampaignApiUrl.SCHEDULE


class TestScheduleCampaignUsingPOST(object):

    # Test URL: /v1/push-campaigns/{id}/schedule [POST]
    def test_schedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        campaign_id = campaign_in_db['id']
        schedule_campaign(campaign_id, data, 'invalid_token', expected_status=(HttpStatus.UNAUTHORIZED,))

    def test_schedule_campaign_with_invalid_data(self, token_first, campaign_in_db, smartlist_first):
        invalid_data_test('post', URL % campaign_in_db['id'], token_first)

    def test_schedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db, smartlist_first):
        data = generate_campaign_schedule_data()
        # Test with invalid or non-existing id
        non_existing_id = sys.maxint
        invalid_ids = [(0, HttpStatus.BAD_REQUEST),
                       (non_existing_id, HttpStatus.NOT_FOUND)]
        for _id, status_code in invalid_ids:
            schedule_campaign(_id, data, token_first, expected_status=(status_code,))

    def test_schedule_campaign_with_put_method(self, token_first, campaign_in_db, smartlist_first):
        """
        Test forbidden error. To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        """
        data = generate_campaign_schedule_data()
        reschedule_campaign(campaign_in_db['id'], data, token_first,
                            expected_status=(HttpStatus.FORBIDDEN,))

    def test_schedule_campaign_with_missing_fields_in_schedule_data(self, token_first, campaign_in_db,
                                                           smartlist_first):
        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['start_datetime']
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(HttpStatus.BAD_REQUEST,))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['end_datetime']
        response = schedule_campaign(campaign_in_db['id'], data, token_first,
                                     expected_status=(HttpStatus.BAD_REQUEST,))
        error = response['error']
        assert 'end_datetime' in error['message']

    def test_schedule_compaign_with_invalid_datetime_format(self, token_first, campaign_in_db,
                                                           smartlist_first):
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        start = datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(HttpStatus.BAD_REQUEST,))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        end = datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        schedule_campaign(campaign_in_db['id'], data, token_first,
                          expected_status=(HttpStatus.BAD_REQUEST,))

    def test_schedule_a_campaign_with_valid_data(self, candidate_first, smartlist_first, campaign_in_db, talent_pool,
                                                 token_first, candidate_device_first):

        # retry(get_smartlist_candidates, attempts=20, sleeptime=3, max_sleeptime=60,
        #       sleepscale=1, retry_exceptions=(AssertionError,), args=(smartlist_first['id'], token_first),
        #       kwargs={'candidates_count': 1})
        data = generate_campaign_schedule_data()
        response = schedule_campaign(campaign_in_db['id'], data, token_first,
                                     expected_status=(HttpStatus.OK,))
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        retry(assert_campaign_blasts, max_sleeptime=60, sleeptime=3, attempts=20,
              sleepscale=1, retry_exceptions=(AssertionError,), args=(campaign_in_db['id'], token_first))

    def test_schedule_a_campaign_with_user_from_same_domain(self, smartlist_same_domain, campaign_data,  talent_pool,
                                                            token_first, token_same_domain,  candidate_device_first):

        # retry(get_smartlist_candidates, attempts=20, sleeptime=3, max_sleeptime=60,
        #       sleepscale=1, retry_exceptions=(AssertionError,), args=(smartlist_same_domain['id'], token_same_domain),
        #       kwargs={'candidates_count': 1})

        data = campaign_data.copy()
        data['smartlist_ids'] = [smartlist_same_domain['id']]
        campaign_id = create_campaign(data, token_first)['id']
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        response = schedule_campaign(campaign_id, data, token_same_domain,
                                     expected_status=(HttpStatus.OK,))
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        retry(assert_campaign_blasts, max_sleeptime=60, sleeptime=3, attempts=20,
              sleepscale=1, retry_exceptions=(AssertionError,), args=(campaign_id, token_first))

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
        schedule_campaign(campaign_in_db['id'], data, token_second, expected_status=(HttpStatus.FORBIDDEN,))


class TestRescheduleCampaignUsingPUT(object):

    # Test URL: /v1/push-campaigns/{id}/schedule [PUT]
    def test_reschedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        campaign_id = campaign_in_db['id']
        reschedule_campaign(campaign_id, data, 'invalid_token', expected_status=(HttpStatus.UNAUTHORIZED,))

    def test_reschedule_campaign_with_other_user(self, token_second, campaign_in_db):
        """
        Test with a valid campaign but user is not owner of campaign
        Here we created campaign with user whose Auth token_first is "token_first"
        and we want to reschedule this campaign using different token_first "token_second"
        """
        data = generate_campaign_schedule_data()
        reschedule_campaign(campaign_in_db['id'], data, token_second,
                            expected_status=(HttpStatus.FORBIDDEN,))

    def test_reschedule_campaign_with_invalid_data(self, token_first, campaign_in_db, smartlist_first):
        invalid_data_test('put', URL % campaign_in_db['id'], token_first)

    def test_reschedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db,
                                                          smartlist_first,
                                                          schedule_a_campaign):
        data = generate_campaign_schedule_data()

        # Test with invalid integer id
        # Test for 404, Schedule a campaign which does not exists or id is invalid
        non_existing_id = sys.maxint
        invalid_ids = [(0, HttpStatus.BAD_REQUEST),
                       (non_existing_id, HttpStatus.NOT_FOUND)]
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
                          expected_status=(HttpStatus.FORBIDDEN,))

    def test_reschedule_campaign_with_missing_fields_in_schedule_data(self, token_first, campaign_in_db,
                                                           smartlist_first, schedule_a_campaign):

        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['start_datetime']
        response = reschedule_campaign(campaign_in_db['id'], data, token_first,
                                       expected_status=(HttpStatus.BAD_REQUEST,))
        error = response['error']
        assert 'start_datetime' in error['message']

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        del data['end_datetime']
        response = reschedule_campaign(campaign_in_db['id'], data, token_first,
                                       expected_status=(HttpStatus.BAD_REQUEST,))
        error = response['error']
        assert 'end_datetime' in error['message']

    def test_reschedule_campaign_with_invalid_datetime_format(self, token_first, campaign_in_db,
                                                            smartlist_first, schedule_a_campaign):
        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        start = datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        reschedule_campaign(campaign_in_db['id'], data, token_first,
                            expected_status=(HttpStatus.BAD_REQUEST,))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        end = datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        reschedule_campaign(campaign_in_db['id'], data, token_first,
                            expected_status=(HttpStatus.BAD_REQUEST,))

    def test_reschedule_campaign_with_valid_data(self, token_first, campaign_in_db, talent_pool, candidate_first,
                                             smartlist_first, schedule_a_campaign):
        retry(assert_campaign_blasts, max_sleeptime=60, sleeptime=3, attempts=20,
              sleepscale=1, retry_exceptions=(AssertionError,), args=(campaign_in_db['id'], token_first))

        data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
        response = send_request('put', PushCampaignApiUrl.SCHEDULE % campaign_in_db['id'], token_first, data)
        assert response.status_code == 200
        response = response.json()
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        retry(assert_campaign_blasts, max_sleeptime=60, sleeptime=3, attempts=20,
              sleepscale=1, retry_exceptions=(AssertionError,), args=(campaign_in_db['id'], token_first),
              kwargs={'expected_count': 2})

    def test_reschedule_a_campaign_with_user_from_same_domain(self, token_first, token_same_domain,
                                                            campaign_in_db, schedule_a_campaign):

        data = generate_campaign_schedule_data()
        reschedule_campaign(campaign_in_db['id'], data, token_same_domain,
                            expected_status=(HttpStatus.FORBIDDEN,))


class TestUnscheduleCamapignUsingDELETE(object):

    # Test URL: /v1/push-campaigns/{id}/schedule [DELETE]
    def test_unschedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first,
                                                    schedule_a_campaign):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('delete',  URL % campaign_in_db['id'], data)

    def test_unschedule_campaign_with_other_user(self, token_second, campaign_in_db):
        # Test with a valid campaign but user is not owner of campaign
        # Here we created campaign with user whose Auth token_first is "token_first"
        # and we have a a test user token_first "test_auth_token" to test ownership
        unschedule_campaign(campaign_in_db['id'], token_second, expected_status=(HttpStatus.FORBIDDEN,))

    def test_unschedule_campaign_with_other_user_but_same_domain(self, token_same_domain,
                                                                 campaign_in_db):
        """
        Test with a valid campaign and user is not owner of campaign but from same domain
        This user should be allowed to unschedule the campaign
        Here we created campaign with user whose Auth token_first is "token_first"
        """
        unschedule_campaign(campaign_in_db['id'], token_same_domain, expected_status=(HttpStatus.OK,))

    def test_unschedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db):
        # Test with invalid integer id
        non_existing_id = sys.maxint
        invalid_ids = [(0, HttpStatus.BAD_REQUEST),
                       (non_existing_id, HttpStatus.NOT_FOUND)]
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
        unschedule_campaign(campaign_in_db['id'], token_first, expected_status=(HttpStatus.OK,))


def assert_campaign_blasts(campaign_id, token, expected_count=1):
    response = get_blasts(campaign_id, token, expected_status=(HttpStatus.OK,))
    blasts = response['blasts']
    return len(blasts) == expected_count

