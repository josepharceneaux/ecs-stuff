"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.routes import SchedulerApiUrl
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test, send_request

URL = PushCampaignApiUrl.SCHEDULE


class TestScheduleCampaignUsingPOST(object):

    # Test URL: /v1/campaigns/{id}/schedule [POST]
    def test_schedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('post',  URL % campaign_in_db['id'],
                         'invalid_token', data)

    def test_schedule_campaign_with_invalid_data(self, token_first, campaign_in_db, smartlist_first):
        invalid_data_test('post', URL % campaign_in_db['id'], token_first)

    def test_schedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db, smartlist_first):
        data = generate_campaign_schedule_data()
        # Test with invalid or non-existing id
        non_existing_id = campaign_in_db['id'] + 10000
        invalid_ids = [(0, INVALID_USAGE),
                       (non_existing_id, NOT_FOUND)]
        for _id, status_code in invalid_ids:
            response = send_request('post', URL % _id, token_first, data)
            assert response.status_code == status_code

    def test_schedule_campaign_with_other_user(self, token_second, campaign_in_db):
        # Test with a valid campaign but user is not owner of campaign
        # Here we created campaign with user whose Auth token_first is "token_first"
        # and we want to schedule this campaign with other user with token_first "token_second"
        data = generate_campaign_schedule_data()
        response = send_request('post', URL
                                % campaign_in_db['id'], token_second, data)
        assert response.status_code == FORBIDDEN

    def test_schedule_campaign_with_put_method(self, token_first, campaign_in_db, smartlist_first):
        # Test forbidden error. To schedule a task first time, we have to send POST,
        # but we will send request using PUT which is for update and will validate error
        data = generate_campaign_schedule_data()
        response = send_request('put', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == FORBIDDEN

    def test_schedule_campaign_with_missing_fields_in_schedule_data(self, token_first, campaign_in_db,
                                                           smartlist_first):
        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data()
        del data['start_datetime']
        response = send_request('post', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE

        data = generate_campaign_schedule_data()
        del data['end_datetime']
        response = send_request('post', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'end_datetime' in error['message']

    def test_schedule_compaign_with_invalid_datetime_format(self, token_first, campaign_in_db,
                                                           smartlist_first):
        data = generate_campaign_schedule_data()
        start = datetime.datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        response = send_request('post', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'Invalid DateTime' in error['message']

        data = generate_campaign_schedule_data()
        end = datetime.datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        response = send_request('post', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'Invalid DateTime' in error['message']

    def test_schedule_a_campaign_with_valid_data(self, token_first, campaign_in_db, smartlist_first):

        data = generate_campaign_schedule_data()
        response = send_request('post', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == OK
        response = response.json()
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        time.sleep(3 * SLEEP_TIME)

        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
        assert response.status_code == 200
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        blast = blasts[0]
        # One send expected since only one candidate is associated with campaign
        assert blast['sends'] == 1

        # Now remove the task from scheduler
        response = send_request('delete', SchedulerApiUrl.TASK % task_id, token_first)
        assert response.status_code == OK, "Unable to remove task from scheduler with " \
                                           "id %s" % task_id


class TestRescheduleCampaignUsingPUT(object):

    # Test URL: /v1/campaigns/{id}/schedule [PUT]
    def test_reschedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('put',  URL % campaign_in_db['id'],
                         'invalid_token', data)

    def test_reschedule_campaign_with_other_user(self, token_second, campaign_in_db):
        # Test with a valid campaign but user is not owner of campaign
        # Here we created campaign with user whose Auth token_first is "token_first"
        # and we want to reschedule this campaign using different token_first "token_second"
        data = generate_campaign_schedule_data()
        response = send_request('put', URL
                                % campaign_in_db['id'], token_second, data)
        assert response.status_code == FORBIDDEN

    def test_reschedule_campaign_with_invalid_data(self, token_first, campaign_in_db, smartlist_first):
        invalid_data_test('put', URL % campaign_in_db['id'], token_first)

    def test_reschedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db,
                                                          smartlist_first,
                                                          schedule_a_campaign):
        data = generate_campaign_schedule_data()

        # Test with invalid integer id
        # Test for 404, Schedule a campaign which does not exists or id is invalid
        non_existing_id = campaign_in_db['id'] + 10000
        invalid_ids = [(0, INVALID_USAGE),
                       (non_existing_id, NOT_FOUND)]
        for _id, status_code in invalid_ids:
            response = send_request('put', URL % _id, token_first, data)
            assert response.status_code == status_code

    def test_reschedule_campaign_with_post_method(self, token_first, campaign_in_db, smartlist_first,
                                                  schedule_a_campaign):
        # Test forbidden error. To schedule a task first time, we have to send POST,
        # but we will send request using PUT which is for update and will validate error
        data = schedule_a_campaign
        response = send_request('post', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == FORBIDDEN

    def test_reschedule_campaign_with_missing_fields_in_schedule_data(self, token_first, campaign_in_db,
                                                           smartlist_first, schedule_a_campaign):

        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data()
        del data['start_datetime']
        response = send_request('put', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert error['message'] == 'start_datetime is required field.'

        data = generate_campaign_schedule_data()
        del data['end_datetime']
        response = send_request('put', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'end_datetime' in error['message']

    def test_reschedule_campaign_with_invalid_datetime_format(self, token_first, campaign_in_db,
                                                            smartlist_first, schedule_a_campaign):
        data = generate_campaign_schedule_data()
        start = datetime.datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        response = send_request('put', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert error['message'] == 'Invalid DateTime: Kindly specify UTC datetime in ' \
                                   'ISO-8601 format like 2015-10-08T06:16:55Z. ' \
                                   'Given Date is %s' % data['start_datetime']

        data = generate_campaign_schedule_data()
        end = datetime.datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        response = send_request('put', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'Invalid DateTime' in error['message']

    def test_reschedule_campaign_with_valid_data(self, token_first, campaign_in_db, smartlist_first,
                                                 schedule_a_campaign):

        data = generate_campaign_schedule_data()
        response = send_request('put', URL
                                % campaign_in_db['id'], token_first, data)
        assert response.status_code == OK
        response = response.json()
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        assert response['message'] == 'Campaign(id:%s) has been re-scheduled.' \
                                      % campaign_in_db['id']
        time.sleep(3 * SLEEP_TIME)
        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
        assert response.status_code == 200
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        blast = blasts[0]
        # One send expected since only one candidate is associated with campaign
        assert blast['sends'] == 1

        # Now remove the task from scheduler
        response = send_request('delete', SchedulerApiUrl.TASK % task_id, token_first)
        assert response.status_code == OK, "Unable to remove task from scheduler with " \
                                           "id %s" % task_id


class TestUnscheduleCamapignUsingDELETE(object):

    # Test URL: /v1/campaigns/{id}/schedule [DELETE]
    def test_unschedule_campaign_with_invalid_token(self, campaign_in_db, smartlist_first,
                                                    schedule_a_campaign):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('delete',  URL % campaign_in_db['id'],
                         'invalid_token', data)

    def test_unschedule_campaign_with_other_user(self, token_second, campaign_in_db):
        # Test with a valid campaign but user is not owner of campaign
        # Here we created campaign with user whose Auth token_first is "token_first"
        # and we have a a test user token_first "test_auth_token" to test ownership
        response = send_request('delete', URL
                                % campaign_in_db['id'], token_second)
        assert response.status_code == FORBIDDEN

    def test_unschedule_campaign_with_invalid_campaign_id(self, token_first, campaign_in_db):
        # Test with invalid integer id
        non_existing_id = campaign_in_db['id'] + 10000
        invalid_ids = [(0, INVALID_USAGE),
                       (non_existing_id, NOT_FOUND)]
        for _id, status_code in invalid_ids:
            response = send_request('delete', URL % _id, token_first)
            assert response.status_code == status_code

    def test_unschedule_a_campaign(self, token_first, campaign_in_db, smartlist_first,
                                   schedule_a_campaign):

        response = send_request('delete', URL
                                % campaign_in_db['id'], token_first)
        assert response.status_code == OK
        response = response.json()
        assert response['message'] == 'Campaign(id:%s) has been unschedule.' \
                                      % campaign_in_db['id']

        response = send_request('delete', URL
                                % campaign_in_db['id'], token_first)
        assert response.status_code == OK
        response = response.json()
        assert 'unschedule' in response['message']