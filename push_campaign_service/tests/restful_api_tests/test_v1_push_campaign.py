"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.common.models.candidate import Candidate
from push_campaign_service.modules.constants import TEST_DEVICE_ID
from push_campaign_service.modules.custom_exceptions import *
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


class TestCreateCampaign(object):

    # URL: /v1/campaigns [POST]
    def test_create_campaign(self, auth_data, campaign_data, test_smartlist):
        """
        This method tests push campaign creation endpoint.

        :param auth_data: token, validity_status
        :param campaign_data: dict
        :param test_smartlist: Smartlist
        :return:
        """
        token, is_valid = auth_data
        if is_valid:
            invalid_data_test('post', PushCampaignApiUrl.CAMPAIGNS, token)
            # First test with missing keys
            for key in ['name', 'body_text', 'url', 'smartlist_ids']:
                data = campaign_data.copy()
                data['smartlist_ids'] = [test_smartlist.id]
                missing_key_test(data, key, token)

            # Success case. Send a valid data and campaign should be created (201)
            data = campaign_data.copy()
            data['smartlist_ids'] = [test_smartlist.id]
            response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
            assert response.status_code == 201, 'Push campaign has been created'
            json_response = response.json()
            _id = json_response['id']
            assert json_response['message'] == 'Push campaign was created successfully'
            assert response.headers['Location'] == PushCampaignApiUrl.CAMPAIGN % _id
            campaign_data['id'] = _id
        else:
            unauthorize_test('post', PushCampaignApiUrl.CAMPAIGNS, token, campaign_data)

    # URL: /v1/campaigns/ [GET]
    def test_get_list_of_zero_campaigns(self, auth_data):
        """
        This method tests get list of push campaign created by this user.
        At this point, test user has no campaign created, so we will get an empty list
        :param auth_data: token, validity_status
        :return:
        """
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushCampaignApiUrl.CAMPAIGNS, token)
            assert response.status_code == OK, 'Status code is not 200'
            json_response = response.json()

            assert json_response['count'] == 0, 'Campaign Count should be 0 this time'
            assert len(json_response['campaigns']) == 0, 'Got an empty list of campaigns'
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGNS, token)

    # URL: /v1/campaigns [GET]
    def test_get_list_of_one_campaign(self, auth_data, campaign_in_db):
        """
        This method tests get list of push campaign created by this user.
        This time we will get one campaign in list that is created by `campaign_in_db` fixture
        :param auth_data: token, validity_status
        :type auth_data: tuple
        :param test_campaign: push campaign object
        :type test_campaign: PushCampaign
        :return:
        """
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushCampaignApiUrl.CAMPAIGNS, token)
            assert response.status_code == OK, 'Status code ok'
            json_response = response.json()

            assert json_response['count'] == 1, 'Campaign Count should be 1 this time'
            assert len(json_response['campaigns']) == 1, 'Got one campaign in list'
            campaign = json_response['campaigns'][0]
            assert campaign_in_db.body_text == campaign['body_text']
            assert campaign_in_db.name == campaign['name']
            assert campaign_in_db.url == campaign['url']
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGNS, token)


class TestCampaignById(object):

    # URL: /v1/campaigns/:id [GET]
    def test_get_by_id(self, auth_data, campaign_in_db):
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)
            assert response.status_code == OK, 'Status code is not 200'
            json_response = response.json()
            campaign = json_response['campaign']
            assert campaign_in_db.id == campaign['id']
            assert campaign_in_db.body_text == campaign['body_text']
            assert campaign_in_db.name == campaign['name']
            assert campaign_in_db.url == campaign['url']
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)

    # update campaign test
    # URL: /v1/campaigns/:id [PUT]
    def test_put_by_id(self, auth_data, campaign_in_db, campaign_data, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            # First get already created campaign
            response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)
            assert response.status_code == OK, 'Status code is not 200'
            json_response = response.json()
            campaign = json_response['campaign']
            compare_campaign_data(campaign_in_db, campaign)
            invalid_data_test('put', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)

            # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
            data = generate_campaign_data()
            data['smartlist_ids'] = [test_smartlist.id]
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            for _id in [0, last_obj.id + 100]:
                response = send_request('put', PushCampaignApiUrl.CAMPAIGN % _id, token, data)
                assert response.status_code == NOT_FOUND, 'ResourceNotFound exception should be raised'
                assert response.json()['error']['message'] == 'Campaign not found with id %s' % _id

            # Test invalid field
            data.update(**generate_campaign_data())
            data['invalid_field_name'] = 'Any Value'
            response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token, data)
            assert response.status_code == INVALID_USAGE, 'InvalidUsage exception should be raised'
            error = response.json()['error']
            assert error['message'] == 'Invalid field in campaign data'
            assert error['invalid_field'] == 'invalid_field_name'

            del data['invalid_field_name']
            smartlist_ids = data['smartlist_ids']

            # Test valid fields with invalid/ empty values
            for key in ['name', 'body_text', 'url', 'smartlist_ids']:
                invalid_value_test(data, key, token, campaign_in_db.id)

            # Test positive case with valid data
            data.update(**generate_campaign_data())
            data['smartlist_ids'] = smartlist_ids
            response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token, data)
            assert response.status_code == OK, 'Campaign was not updated successfully'
            data['id'] = campaign_in_db.id

            # Now get campaign from API and compare data.
            response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)
            assert response.status_code == OK, 'Status code is not 200'
            json_response = response.json()
            campaign = json_response['campaign']
            # Compare sent campaign dict and campaign dict returned by API.
            compare_campaign_data(data, campaign)
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)


class TestSendCmapign(object):
    # Send a campaign
    # URL: /v1/campaigns/<int:campaign_id>/send [POST]
    def test_send_a_camapign(self, auth_data, campaign_in_db, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            # 404 case. Send a non existing campaign id
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            invalid_id = last_obj.id + 100
            response = send_request('post', PushCampaignApiUrl.SEND % invalid_id, token)
            assert response.status_code == NOT_FOUND, 'Push campaign should not exists with this id'

            # 200 case: Campaign Sent successfully
            response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db.id, token)
            assert response.status_code == OK, 'Push campaign has not been sent'
            response = response.json()
            assert response['message'] == 'Campaign(id:%s) is being sent to candidates' \
                                          % campaign_in_db.id

            # Wait for 20 seconds to run celery which will send campaign and creates blast
            time.sleep(2 * SLEEP_TIME)
            # Update session to get latest changes in database. Celery has added some records
            db.session.commit()
            # There should be only one blast for this campaign
            blasts = campaign_in_db.blasts.all()
            assert len(blasts) == 1
            assert blasts[0].sends == 1, 'Campaign should have been sent to one candidate'
        else:
            unauthorize_test('post', PushCampaignApiUrl.SEND % campaign_in_db.id, token)

    def test_send_campaign_without_smartlist(self, auth_data, campaign_in_db):
        token, is_valid = auth_data
        if is_valid:
            response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db.id, token)
            assert response.status_code == INTERNAL_SERVER_ERROR, 'Status code is not 500'
            error = response.json()['error']
            assert error['code'] == NO_SMARTLIST_ASSOCIATED
        # 404 status code has been tested in above test

    def test_send_campaign_to_smartlist_with_no_candidates(self, auth_data, campaign_in_db,
                                                           test_smartlist_with_no_candidates):
        token, is_valid = auth_data
        if is_valid:
            response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db.id, token)
            assert response.status_code == INTERNAL_SERVER_ERROR, 'status code is not 500'
            error = response.json()['error']
            assert error['code'] == NO_CANDIDATE_ASSOCIATED
        # 404 status code has been tested in above test


class TestCampaignBlasts(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts [GET]
    def test_get_campaign_blasts(self, auth_data, campaign_in_db, test_smartlist,
                                 campaign_blasts_count):
        token, is_valid = auth_data
        if is_valid:
            # Wait for campaigns to be sent
            time.sleep(SLEEP_TIME)

            # 404 Case, Campaign not found
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            invalid_id = last_obj.id + 100
            response = send_request('get', PushCampaignApiUrl.BLASTS % invalid_id, token)
            assert response.status_code == NOT_FOUND, 'Resource should not be found'

            # 200 case: Campaign Blast successfully
            response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db.id, token)
            assert response.status_code == OK, 'Could not get campaign blasts info'
            response = response.json()
            assert response['count'] == campaign_blasts_count
            assert len(response['blasts']) == campaign_blasts_count
        else:
            unauthorize_test('get', PushCampaignApiUrl.BLASTS % campaign_in_db.id, token)


class TestCampaignSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_sends(self, auth_data, campaign_in_db, test_smartlist,
                                campaign_blasts_count):
        token, is_valid = auth_data
        if is_valid:
            # Wait for campaigns to be sent
            time.sleep(2 * SLEEP_TIME)

            # 404 Case, Campaign not found
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            invalid_id = last_obj.id + 100
            response = send_request('get', PushCampaignApiUrl.SENDS % invalid_id, token)
            assert response.status_code == NOT_FOUND, 'Resource should not be found'
            # 200 case: Got Campaign Sends successfully
            response = send_request('get', PushCampaignApiUrl.SENDS % campaign_in_db.id, token)
            assert response.status_code == OK, 'Could not get campaign sends info'
            response = response.json()
            # Since each blast have one send, so total sends will be equal to number of blasts
            assert response['count'] == campaign_blasts_count
            assert len(response['sends']) == campaign_blasts_count

        else:
            unauthorize_test('get', PushCampaignApiUrl.SENDS % campaign_in_db.id, token)


class TestCampaignBlastSends(object):

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends [GET]
    def test_get_campaign_blast_sends(self, auth_data, campaign_in_db, test_smartlist,
                                      campaign_blasts_count):
        token, is_valid = auth_data
        if is_valid:
            # Wait for campaigns to be sent
            time.sleep(SLEEP_TIME)
            last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            last_blast = PushCampaignBlast.query.order_by(PushCampaignBlast.id.desc()).first()
            invalid_campaign_id = last_campaign.id + 100
            invalid_blast_id = last_blast.id + 100
            for blast in campaign_in_db.blasts.all():
                # 404 Case, Campaign not found
                # 404 with invalid campaign id and valid blast id
                response = send_request('get', PushCampaignApiUrl.BLASTS_SENDS
                                        % (invalid_campaign_id, blast.id), token)
                assert response.status_code == NOT_FOUND, 'Resource should not be found'

                # 404 with valid campaign id but invalid blast id
                response = send_request('get', PushCampaignApiUrl.BLASTS_SENDS
                                        % (campaign_in_db.id,invalid_blast_id), token)
                assert response.status_code == NOT_FOUND, 'Resource should not be found'

                # 200 case: Got Campaign Sends successfully
                response = send_request('get', PushCampaignApiUrl.BLASTS_SENDS
                                        % (campaign_in_db.id, blast.id), token)
                assert response.status_code == OK, 'Could not get campaign sends info'
                response = response.json()
                # Since each blast have one send, so total sends will be equal to number of blasts
                assert response['count'] == 1
                assert len(response['sends']) == 1

        else:
            # We are testing 401 here. so campaign and blast ids will not matter.
            unauthorize_test('get',  PushCampaignApiUrl.BLASTS_SENDS % (campaign_in_db.id, 1), token)


class TestRegisterCandidateDevice(object):

    # Test URL: /v1/devices [POST]
    def test_associate_a_device_to_candidate(self, auth_data, test_candidate):
        token, is_valid = auth_data
        if is_valid:
            invalid_data_test('post', PushCampaignApiUrl.DEVICES, token)
            last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
            invalid_candiate_id = last_candidate.id + 100
            valid_device_id = TEST_DEVICE_ID
            invalid_candidate_data = {
                '': (INVALID_USAGE, 'candidate_id is not given in post data'),
                0: (INVALID_USAGE, 'candidate_id is not given in post data'),
                -1: (NOT_FOUND, 'Unable to associate device with a non existing candidate id: -1'),
                invalid_candiate_id: (NOT_FOUND, 'Unable to associate device with a non existing '
                                                 'candidate id: %s' % invalid_candiate_id)
            }
            invalid_device_data = {
                '': (INVALID_USAGE, 'device_id is not given in post data'),
                0: (INVALID_USAGE, 'device_id is not given in post data'),
                'invalid_id': (NOT_FOUND, 'Device is not registered with OneSignal '
                                          'with id invalid_id')
            }
            for key in invalid_candidate_data:
                data = dict(candidate_id=key, device_id=valid_device_id)
                response = send_request('post', PushCampaignApiUrl.DEVICES, token, data)
                status_code, message = invalid_candidate_data[key]
                assert response.status_code == status_code, 'exception raised'
                error = response.json()['error']
                assert error['message'] == message

            for key in invalid_device_data:
                data = dict(candidate_id=test_candidate.id, device_id=key)
                response = send_request('post', PushCampaignApiUrl.DEVICES, token, data)
                status_code, message = invalid_device_data[key]
                assert response.status_code == status_code, 'exception raised'
                error = response.json()['error']
                assert error['message'] == message

            data = dict(candidate_id=test_candidate.id, device_id=valid_device_id)
            response = send_request('post', PushCampaignApiUrl.DEVICES, token, data)
            assert response.status_code == OK, 'Could not associate device to candidate'
            response = response.json()
            assert response['message'] == 'Device registered successfully with candidate (id: %s)' \
                                          % test_candidate.id

            # A device has been associated to test_candidate through API but in tests
            # we need to refresh our session to get those changes (using relationship)
            db.session.commit()
            devices = test_candidate.devices.all()
            assert len(devices) == 1, 'One device should be associated to this test candidate'
            device = devices[0]
            assert device.one_signal_device_id == valid_device_id

        else:
            # We are testing 401 here. so campaign and blast ids will not matter.
            unauthorize_test('post',  PushCampaignApiUrl.DEVICES, token)


class TestScheduleCampaignResource(object):

    # Test URL: /v1/campaigns/{id}/schedule [POST]
    def test_schedule_a_campaign(self, auth_data, campaign_in_db, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            invalid_data_test('post', PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token)
            data = generate_campaign_schedule_data()

            # Test with invalid integer id
            invalid_ids = [(0, INVALID_USAGE, 'campaign_id should be a positive number'),
                           (-1, NOT_FOUND, None)]
            for _id, status_code, message in invalid_ids:
                response = send_request('post', PushCampaignApiUrl.SCHEDULE % _id, token, data)
                assert response.status_code == status_code
                # Test message when it is returned by Resource. in case of -1, URL will
                # not be hit but service will return html response saying Not found
                if message:
                    error = response.json()['error']
                    assert error['message'] == message

            # Now test for 404, Schedule a campaign which does not exists
            last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            non_existing_id = last_campaign.id + 100
            response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                    % non_existing_id, token, data)
            assert response.status_code == NOT_FOUND

            # Test with a valid campaign but user is not owner of campaign
            # Here we created campaign with user whose Auth token is "token"
            # and we have a a test user token "test_auth_token" to test ownership
            # response = send_request('post', PushCampaignApiUrl.SCHEDULE
            #                         % campaign_in_db.id, test_auth_token, data)
            # assert response.status_code == FORBIDDEN
            # error = response.json['error']
            # assert error['message'] == 'You are not the owner of Push campaign(id:%s)' \
            #                            % campaign_in_db

            # Test forbidden error. To schedule a task first time, we have to send POST,
            # but we will send request using PUT which is for update and will validate error
            response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                    % campaign_in_db.id, token, data)
            assert response.status_code == FORBIDDEN
            error = response.json()['error']
            assert error['message'] == 'Use POST method instead to schedule campaign first time'

            # Test missing start_datetime field which is mandatory to schedule a campaign
            del data['start_datetime']
            response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                    % campaign_in_db.id, token, data)
            assert response.status_code == INVALID_USAGE
            error = response.json()['error']
            assert error['message'] == 'start_datetime is required field.'

            # Test with start_datetime in past. It will raise an error. start_datetime
            # should be in future
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
            del data['end_datetime']
            response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                    % campaign_in_db.id, token, data)
            assert response.status_code == INVALID_USAGE
            error = response.json()['error']
            assert error['message'] == 'end_datetime is required field to create periodic task'

            # start = datetime.datetime.utcnow() - datetime.timedelta(seconds=100)
            # data['start_datetime'] = to_utc_str(start)
            # response = send_request('post', PushCampaignApiUrl.SCHEDULE
            #                         % campaign_in_db.id, token, data)
            # assert response.status_code == INVALID_USAGE
            # error = response.json()['error']
            # assert error['message'] == "Given datetime(%s) should be in future" % start

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

        else:
            # data not needed here but just to be consistent with other requests of
            # this resource test
            data = generate_campaign_schedule_data()
            unauthorize_test('post',  PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token, data)

    # Test URL: /v1/campaigns/{id}/schedule [PUT]
    def test_reschedule_a_campaign(self, auth_data, campaign_in_db, test_smartlist,
                                   schedule_a_campaign):
        token, is_valid = auth_data
        if is_valid:
            invalid_data_test('put', PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token)
            # data = {
            #     "start_datetime": to_utc_str(campaign_in_db.start_datetime),
            #     "end_datetime": to_utc_str(campaign_in_db.end_datetime),
            #     "frequency": campaign_in_db.frequency
            # }
            data = generate_campaign_schedule_data()

            # Test with invalid integer id
            invalid_ids = [(0, INVALID_USAGE, 'campaign_id should be a positive number'),
                           (-1, NOT_FOUND, None)]
            for _id, status_code, message in invalid_ids:
                response = send_request('put', PushCampaignApiUrl.SCHEDULE % _id, token, data)
                assert response.status_code == status_code
                # Test message when it is returned by Resource. in case of -1, URL will
                # not be hit but service will return html response saying Not found
                if message:
                    error = response.json()['error']
                    assert error['message'] == message

            # Now test for 404, Schedule a campaign which does not exists
            last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            non_existing_id = last_campaign.id + 100
            response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                    % non_existing_id, token, data)
            assert response.status_code == NOT_FOUND

            # Test forbidden error. To schedule a task first time, we have to send POST,
            # but we will send request using PUT which is for update and will validate error
            data = schedule_a_campaign
            response = send_request('post', PushCampaignApiUrl.SCHEDULE
                                    % campaign_in_db.id, token, data)
            assert response.status_code == FORBIDDEN
            error = response.json()['error']
            assert error['message'] == 'Use PUT method instead to update already scheduled task'

            # Test missing start_datetime field which is mandatory to schedule a campaign
            del data['start_datetime']
            response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                    % campaign_in_db.id, token, data)
            assert response.status_code == INVALID_USAGE
            error = response.json()['error']
            assert error['message'] == 'start_datetime is required field.'

            # Test with start_datetime in past. It will raise an error. start_datetime
            # should be in future
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
            del data['end_datetime']
            response = send_request('put', PushCampaignApiUrl.SCHEDULE
                                    % campaign_in_db.id, token, data)
            assert response.status_code == INVALID_USAGE
            error = response.json()['error']
            assert error['message'] == 'end_datetime is required field to create periodic task'

            data = generate_campaign_schedule_data()
            response = send_request('put', PushCampaignApiUrl.SCHEDULE
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

        else:
            # data not needed here but just to be consistent with other requests of
            # this resource test
            data = generate_campaign_schedule_data()
            unauthorize_test('put',  PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token, data)
