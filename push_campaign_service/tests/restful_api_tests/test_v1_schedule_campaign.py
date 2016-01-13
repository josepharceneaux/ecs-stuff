"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.tests.helper_methods import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi
from push_campaign_service.common.routes import SchedulerApiUrl
# Constants
API_URL = PushCampaignApi.HOST_NAME
VERSION = PushCampaignApi.VERSION

SLEEP_TIME = 20
OK = 200
INVALID_USAGE = 400
NOT_FOUND = 404
FORBIDDEN = 403
INTERNAL_SERVER_ERROR = 500


class TestScheduleCampaignUsingPOST(object):

    # Test URL: /v1/campaigns/{id}/schedule [POST]
    def test_schedule_campaign_with_invalid_token(self, campaign_in_db, test_smartlist):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('post',  PushCampaignApiUrl.SCHEDULE % campaign_in_db.id,
                         'invalid_token', data)

    def test_schedule_campaign_with_invalid_data(self, token, campaign_in_db, test_smartlist):
        invalid_data_test('post', PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token)

    def test_schedule_campaign_with_invalid_campaign_id(self, token, campaign_in_db, test_smartlist):
        data = generate_campaign_schedule_data()
        # Test with invalid or non-existing id
        last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
        non_existing_id = last_campaign.id + 100
        invalid_ids = [(0, INVALID_USAGE),
                       (non_existing_id, NOT_FOUND)]
        for _id, status_code in invalid_ids:
            response = send_request('post', PushCampaignApiUrl.SCHEDULE % _id, token, data)
            assert response.status_code == status_code

    # def test_schedule_campaign_with_other_user(self):
        # Test with a valid campaign but user is not owner of campaign
        # Here we created campaign with user whose Auth token is "token"
        # and we have a a test user token "test_auth_token" to test ownership
        # response = send_request('post', PushCampaignApiUrl.SCHEDULE
        #                         % campaign_in_db.id, test_auth_token, data)
        # assert response.status_code == FORBIDDEN
        # error = response.json['error']
        # assert error['message'] == 'You are not the owner of Push campaign(id:%s)' \
        #                            % campaign_in_db

    def test_schedule_campaign_with_put_method(self, token, campaign_in_db, test_smartlist):
        # Test forbidden error. To schedule a task first time, we have to send POST,
        # but we will send request using PUT which is for update and will validate error
        data = generate_campaign_schedule_data()
        response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == FORBIDDEN
        error = response.json()['error']
        assert error['message'] == 'Use POST method instead to schedule campaign first time'

    def test_schedule_campaign_with_missing_fields_in_schedule_data(self, token, campaign_in_db,
                                                           test_smartlist):
        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data()
        del data['start_datetime']
        response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert error['message'] == 'start_datetime is required field.'

        data = generate_campaign_schedule_data()
        del data['end_datetime']
        response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'end_datetime' in error['message']

    def test_schedule_compaign_with_invalid_datetime_format(self, token, campaign_in_db,
                                                           test_smartlist):
        data = generate_campaign_schedule_data()
        start = datetime.datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert error['message'] == 'Invalid DateTime: Kindly specify UTC datetime in ' \
                                   'ISO-8601 format like 2015-10-08T06:16:55Z. ' \
                                   'Given Date is %s' % data['start_datetime']

        data = generate_campaign_schedule_data()
        end = datetime.datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'Invalid DateTime' in error['message']

    def test_schedule_a_campaign_with_valid_data(self, token, campaign_in_db, test_smartlist):

        data = generate_campaign_schedule_data()
        response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == OK
        response = response.json()
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        assert response['message'] == 'Campaign(id:%s) has been scheduled.' % campaign_in_db.id
        time.sleep(3 * SLEEP_TIME)
        #
        db.session.commit()

        blasts = campaign_in_db.blasts.all()
        assert len(blasts) == 1
        blast = blasts[0]
        # One send expected since only one candidate is associated with campaign
        assert blast.sends == 1

        # Now remove the task from scheduler
        response = send_request('delete', SchedulerApiUrl.TASK % task_id, token)
        assert response.status_code == OK, "Unable to remove task from scheduler with " \
                                           "id %s" % task_id


class TestRescheduleCampaignUsingPUT(object):

    # Test URL: /v1/campaigns/{id}/schedule [PUT]
    def test_reschedule_campaign_with_invalid_token(self, campaign_in_db, test_smartlist):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('put',  PushCampaignApiUrl.SCHEDULE % campaign_in_db.id,
                         'invalid_token', data)

    def test_reschedule_campaign_with_invalid_data(self, token, campaign_in_db, test_smartlist):
        invalid_data_test('put', PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token)

    def test_reschedule_campaign_with_invalid_campaign_id(self, token, campaign_in_db,
                                                          test_smartlist,
                                                          schedule_a_campaign):
        data = generate_campaign_schedule_data()

        # Test with invalid integer id
        # Test for 404, Schedule a campaign which does not exists or id is invalid
        last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
        non_existing_id = last_campaign.id + 100
        invalid_ids = [(0, INVALID_USAGE),
                       (non_existing_id, NOT_FOUND)]
        for _id, status_code in invalid_ids:
            response = send_request('put', PushCampaignApiUrl.SCHEDULE % _id, token, data)
            assert response.status_code == status_code

    def test_reschedule_campaign_with_post_method(self, token, campaign_in_db, test_smartlist,
                                                  schedule_a_campaign):
        # Test forbidden error. To schedule a task first time, we have to send POST,
        # but we will send request using PUT which is for update and will validate error
        data = schedule_a_campaign
        response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == FORBIDDEN
        error = response.json()['error']
        assert error['message'] == 'Use PUT method instead to update already scheduled task'

    def test_reschedule_campaign_with_missing_fields_in_schedule_data(self, token, campaign_in_db,
                                                           test_smartlist, schedule_a_campaign):

        # Test missing start_datetime field which is mandatory to schedule a campaign
        data = generate_campaign_schedule_data()
        del data['start_datetime']
        response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert error['message'] == 'start_datetime is required field.'

        data = generate_campaign_schedule_data()
        del data['end_datetime']
        response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'end_datetime' in error['message']

    def test_reschedule_campaign_with_invalid_datetime_format(self, token, campaign_in_db,
                                                            test_smartlist, schedule_a_campaign):
        data = generate_campaign_schedule_data()
        start = datetime.datetime.utcnow()
        data['start_datetime'] = str(start)  # Invalid datetime format
        response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert error['message'] == 'Invalid DateTime: Kindly specify UTC datetime in ' \
                                   'ISO-8601 format like 2015-10-08T06:16:55Z. ' \
                                   'Given Date is %s' % data['start_datetime']

        data = generate_campaign_schedule_data()
        end = datetime.datetime.utcnow()
        data['end_datetime'] = str(end)  # Invalid datetime format
        response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE
        error = response.json()['error']
        assert 'Invalid DateTime' in error['message']

    def test_reschedule_campaign_with_valid_data(self, token, campaign_in_db, test_smartlist,
                                                 schedule_a_campaign):

        data = generate_campaign_schedule_data()
        response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token, data)
        assert response.status_code == OK
        response = response.json()
        assert 'task_id' in response
        assert 'message' in response
        task_id = response['task_id']
        assert task_id
        assert response['message'] == 'Campaign(id:%s) has been re-scheduled.' \
                                      % campaign_in_db.id
        time.sleep(3 * SLEEP_TIME)
        #
        db.session.commit()

        blasts = campaign_in_db.blasts.all()
        assert len(blasts) == 1
        blast = blasts[0]
        # One send expected since only one candidate is associated with campaign
        assert blast.sends == 1

        # Now remove the task from scheduler
        response = send_request('delete', SchedulerApiUrl.TASK % task_id, token)
        assert response.status_code == OK, "Unable to remove task from scheduler with " \
                                           "id %s" % task_id


class TestUnscheduleCamapignUsingDELETE(object):

    # Test URL: /v1/campaigns/{id}/schedule [DELETE]
    def test_unschedule_campaign_with_invalid_token(self, campaign_in_db, test_smartlist,
                                                    schedule_a_campaign):
        # data not needed here but just to be consistent with other requests of
        # this resource test
        data = generate_campaign_schedule_data()
        unauthorize_test('delete',  PushCampaignApiUrl.SCHEDULE % campaign_in_db.id,
                         'invalid_token', data)

    def test_unschedule_campaign_with_invalid_campaign_id(self, token):
        # Test with invalid integer id
        last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
        non_existing_id = last_campaign.id + 100
        invalid_ids = [(0, INVALID_USAGE),
                       (non_existing_id, NOT_FOUND)]
        for _id, status_code in invalid_ids:
            response = send_request('delete', PushCampaignApiUrl.SCHEDULE % _id, token)
            assert response.status_code == status_code

    def test_unschedule_a_campaign(self, token, campaign_in_db, test_smartlist,
                                   schedule_a_campaign):

        response = send_request('delete', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token)
        assert response.status_code == OK
        response = response.json()
        assert response['message'] == 'Campaign(id:%s) has been unschedule.' \
                                      % campaign_in_db.id

        response = send_request('delete', PushCampaignApiUrl.SCHEDULE
                                % campaign_in_db.id, token)
        assert response.status_code == OK
        response = response.json()
        assert 'unschedule' in response['message']