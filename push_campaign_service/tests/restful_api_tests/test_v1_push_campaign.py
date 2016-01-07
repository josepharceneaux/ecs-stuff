"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.common.models.candidate import Candidate
from push_campaign_service.tests.helper_methods import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi
# Constants
API_URL = PushCampaignApi.HOST_NAME
VERSION = PushCampaignApi.VERSION

SLEEP_TIME = 20


class TestCreateCampaign():

    # URL: /v1/campaigns [POST]
    def test_create_campaign(self, auth_data, campaign_data, test_campaign, test_smartlist):
        """
        This method tests push campaign creation endpoint.

        :param auth_data: token, validity_status
        :param campaign_data:
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
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()

            assert json_response['count'] == 0, 'Campaign Count should be 0 this time'
            assert len(json_response['campaigns']) == 0, 'Got an empty list of campaigns'
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGNS, token)

    # URL: /v1/campaigns [GET]
    def test_get_list_of_one_campaign(self, auth_data, test_campaign):
        """
        This method tests get list of push campaign created by this user.
        This time we will get one campaign in list that is created by `test_campaign` fixture
        :param auth_data: token, validity_status
        :type auth_data: tuple
        :param test_campaign: push campaign object
        :type test_campaign: PushCampaign
        :return:
        """
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushCampaignApiUrl.CAMPAIGNS, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()

            assert json_response['count'] == 1, 'Campaign Count should be 1 this time'
            assert len(json_response['campaigns']) == 1, 'Got one campaign in list'
            campaign = json_response['campaigns'][0]
            assert test_campaign.body_text == campaign['body_text']
            assert test_campaign.name == campaign['name']
            assert test_campaign.url == campaign['url']
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGNS, token)


class TestCampaignById():

    # URL: /v1/campaigns/:id [GET]
    def test_get_by_id(self, auth_data, test_campaign):
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()
            campaign = json_response['campaign']
            assert test_campaign.id == campaign['id']
            assert test_campaign.body_text == campaign['body_text']
            assert test_campaign.name == campaign['name']
            assert test_campaign.url == campaign['url']
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token)

    # update campaign test
    # URL: /v1/campaigns/:id [PUT]
    def test_put_by_id(self, auth_data, test_campaign, campaign_data, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            # First get already created campaign
            response = send_request('get', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()
            campaign = json_response['campaign']
            compare_campaign_data(test_campaign, campaign)
            invalid_data_test('put', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token)

            # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
            data = campaign_data.copy()
            data['smartlist_ids'] = [test_smartlist.id]
            if 'user_id' in data: del data['user_id']
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            non_existing_id = last_obj.id + 1
            response = send_request('put', PushCampaignApiUrl.CAMPAIGN % non_existing_id, token, data)
            response.status_code == 404, 'ResourceNotFound exception raised'
            assert response.json()['error']['message'] == 'Campaign not found with id %s' % non_existing_id

            # Test invalid field
            data.update(**generate_campaign_data())
            data['invalid_field_name'] = 'Any Value'
            response = send_request('put', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token, data)
            response.status_code == 400, 'InvalidUsage exception raised'
            error = response.json()['error']
            assert error['message'] == 'Invalid field in campaign data'
            assert error['invalid_field'] == 'invalid_field_name'

            del data['invalid_field_name']
            smartlist_ids = data['smartlist_ids']

            # Test valid fields with invalid/ empty values
            for key in ['name', 'body_text', 'url', 'smartlist_ids']:
                invalid_value_test(data, key, token, test_campaign.id)

            # Test positive case with valid data
            data.update(**generate_campaign_data())
            data['smartlist_ids'] = smartlist_ids
            response = send_request('put', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token, data)
            response.status_code == 200, 'Campaign updated successfully'
            data['id'] = test_campaign.id

            # Now get campaign from API and compare data.
            response = send_request('get', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()
            campaign = json_response['campaign']
            # Compare sent campaign dict and campaign dict returned by API.
            compare_campaign_data(data, campaign)
        else:
            unauthorize_test('get', PushCampaignApiUrl.CAMPAIGN % test_campaign.id, token)


class TestSendCmapign():

    # Send a campaign
    # URL: /v1/campaigns/<int:campaign_id>/send [POST]
    def test_send_a_camapign(self, auth_data, test_campaign, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            # 404 case. Send a non existing campaign id
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            response = send_request('post', PushCampaignApiUrl.SEND % (last_obj.id + 1), token)
            assert response.status_code == 404, 'Push campaign does not exists with this id'

            # 200 case: Campaign Sent successfully
            response = send_request('post', PushCampaignApiUrl.SEND % test_campaign.id, token)
            assert response.status_code == 200, 'Push campaign has been sent'
            response = response.json()
            assert response['message'] == 'Campaign(id:%s) is being sent to candidates' % test_campaign.id

            # Wait for 20 seconds to run celery which will send campaign and creates blast
            time.sleep(2 * SLEEP_TIME)
            # Update session to get latest changes in database. Celery has added some records
            db.session.commit()
            # There should be only one blast for this campaign
            blasts = test_campaign.blasts.all()
            assert len(blasts) == 1
            assert blasts[0].sends == 1, 'Campaign was sent to one candidate'
        else:
            unauthorize_test('post', PushCampaignApiUrl.SEND % test_campaign.id, token)


class TestCampaignBlasts():

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts [GET]
    def test_get_campaign_blasts(self, auth_data, test_campaign, test_smartlist, campaign_blasts_count):
        token, is_valid = auth_data
        if is_valid:
            # Wait for campaigns to be sent
            time.sleep(SLEEP_TIME)

            # 404 Case, Campaign not found
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            response = send_request('get', PushCampaignApiUrl.BLASTS % (last_obj.id + 1), token)
            assert response.status_code == 404, 'Resource not found'
            # 200 case: Campaign Blast successfully
            response = send_request('get', PushCampaignApiUrl.BLASTS % test_campaign.id, token)
            assert response.status_code == 200, 'Successfully got campaign blasts info'
            response = response.json()
            assert response['count'] == campaign_blasts_count
            assert len(response['blasts']) == campaign_blasts_count
        else:
            unauthorize_test('get', PushCampaignApiUrl.BLASTS % test_campaign.id, token)


class TestCampaignSends():

    # Test URL: /v1/campaigns/<int:campaign_id>/sends [GET]
    def test_get_campaign_sends(self, auth_data, test_campaign, test_smartlist, campaign_blasts_count):
        token, is_valid = auth_data
        if is_valid:
            # Wait for campaigns to be sent
            time.sleep(2 * SLEEP_TIME)

            # 404 Case, Campaign not found
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            response = send_request('get', PushCampaignApiUrl.SENDS % (last_obj.id + 1), token)
            assert response.status_code == 404, 'Resource not found'
            # 200 case: Got Campaign Sends successfully
            response = send_request('get', PushCampaignApiUrl.SENDS % test_campaign.id, token)
            assert response.status_code == 200, 'Successfully got campaign sends info'
            response = response.json()
            # Since each blast have one send, so total sends will be equal to number of blasts
            assert response['count'] == campaign_blasts_count
            assert len(response['sends']) == campaign_blasts_count

        else:
            unauthorize_test('get', PushCampaignApiUrl.SENDS % test_campaign.id, token)


class TestCampaignBlastSends():

    # Test URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends [GET]
    def test_get_campaign_blast_sends(self, auth_data, test_campaign, test_smartlist, campaign_blasts_count):
        token, is_valid = auth_data
        if is_valid:
            # Wait for campaigns to be sent
            time.sleep(SLEEP_TIME)
            last_campaign = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            last_blast = PushCampaignBlast.query.order_by(PushCampaignBlast.id.desc()).first()
            for blast in test_campaign.blasts.all():
                # 404 Case, Campaign not found

                # 404 with invalid campaign id and valid blast id
                response = send_request('get', PushCampaignApiUrl.BLASTS_SENDS % ((last_campaign.id + 1),
                                                                                     blast.id), token)
                assert response.status_code == 404, 'Resource not found'

                # 404 with valid campaign id but invalid blast id
                response = send_request('get', PushCampaignApiUrl.BLASTS_SENDS % (test_campaign.id,
                                                                                     (last_blast.id + 1)), token)
                assert response.status_code == 404, 'Resource not found'

                # 200 case: Got Campaign Sends successfully
                response = send_request('get', PushCampaignApiUrl.BLASTS_SENDS % (test_campaign.id, blast.id), token)
                assert response.status_code == 200, 'Successfully got campaign sends info'
                response = response.json()
                # Since each blast have one send, so total sends will be equal to number of blasts
                assert response['count'] == 1
                assert len(response['sends']) == 1

        else:
            # We are testing 401 here. so campaign and blast ids will not matter.
            unauthorize_test('get',  PushCampaignApiUrl.BLASTS_SENDS % (test_campaign.id, 1), token)


class TestRegisterCandidateDevice():

    # Test URL: /v1/devices [POST]
    def test_associate_a_device_to_candidate(self, auth_data, test_candidate):
        token, is_valid = auth_data
        if is_valid:
            invalid_data_test('post', PushCampaignApiUrl.DEVICES, token)
            last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
            invalid_candiate_id = last_candidate.id + 100
            valid_device_id = '56c1d574-237e-4a41-992e-c0094b6f2ded'
            invalid_candidate_data = {
                '': (400, 'candidate_id is not given in post data'),
                0: (400, 'candidate_id is not given in post data'),
                -1: (404, 'Unable to associate device with a non existing candidate id: -1'),
                invalid_candiate_id: (404, 'Unable to associate device with a non existing '
                                           'candidate id: %s' % invalid_candiate_id)
            }
            invalid_device_data = {
                '': (400, 'device_id is not given in post data'),
                0: (400, 'device_id is not given in post data'),
                'invalid_id': (404, 'Device is not registered with OneSignal with id invalid_id'),
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
            assert response.status_code == 200, 'Device was associated to candidate'
            response = response.json()
            assert response['message'] == 'Device registered successfully with candidate (id: %s)' % test_candidate.id

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
