"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports

# Application specific imports
from push_campaign_service.tests.helper_methods import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.models.candidate import Candidate
from push_campaign_service.modules.constants import TEST_DEVICE_ID
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi
# Constants
API_URL = PushCampaignApi.HOST_NAME
VERSION = PushCampaignApi.VERSION

SLEEP_TIME = 20
OK = 200
INVALID_USAGE = 400
NOT_FOUND = 404
FORBIDDEN = 403
INTERNAL_SERVER_ERROR = 500


class TestRegisterCandidateDevice(object):

    def test_associate_device_with_invalid_token(self, test_candidate):
        # We are testing 401 here. so campaign and blast ids will not matter.
        unauthorize_test('post',  PushCampaignApiUrl.DEVICES, 'invalid_token')

    def test_associate_device_with_invalid_data(self, token, test_candidate):
        invalid_data_test('post', PushCampaignApiUrl.DEVICES, token)

    # Test URL: /v1/devices [POST]
    def test_associate_device_with_invalid_candidate_id(self, token, test_candidate):
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
        for key in invalid_candidate_data:
            data = dict(candidate_id=key, device_id=valid_device_id)
            response = send_request('post', PushCampaignApiUrl.DEVICES, token, data)
            status_code, message = invalid_candidate_data[key]
            assert response.status_code == status_code, 'exception raised'
            error = response.json()['error']
            assert error['message'] == message

    def test_associate_device_with_invalid_device_id(self, token, test_candidate):
        invalid_device_data = {
                '': (INVALID_USAGE, 'device_id is not given in post data'),
                0: (INVALID_USAGE, 'device_id is not given in post data'),
                'invalid_id': (NOT_FOUND, 'Device is not registered with OneSignal '
                                          'with id invalid_id')
            }
        for key in invalid_device_data:
            data = dict(candidate_id=test_candidate.id, device_id=key)
            response = send_request('post', PushCampaignApiUrl.DEVICES, token, data)
            status_code, message = invalid_device_data[key]
            assert response.status_code == status_code, 'exception raised'
            error = response.json()['error']
            assert error['message'] == message

    def test_associate_a_device_to_candidate(self, token, test_candidate):
        data = dict(candidate_id=test_candidate.id, device_id=TEST_DEVICE_ID)
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
        assert device.one_signal_device_id == TEST_DEVICE_ID