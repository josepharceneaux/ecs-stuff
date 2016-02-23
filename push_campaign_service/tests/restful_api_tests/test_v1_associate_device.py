# """
# This module contains tests related to Push Campaign RESTful API endpoints.
# """
# # Builtin imports
#
# # Application specific imports
# from push_campaign_service.tests.test_utilities import *
# from push_campaign_service.common.utils.test_utils import unauthorize_test
# from push_campaign_service.common.routes import PushCampaignApiUrl, CandidateApiUrl
# from push_campaign_service.modules.constants import PUSH_DEVICE_ID
#
# URL = CandidateApiUrl.DEVICES
#
#
# class TestRegisterCandidateDevice(object):
#
#     def test_associate_device_with_invalid_token(self, user_same_domain):
#         """
#         Associate device to a candidate with invalid token and it should raise Unauthorized 401
#         :param user_same_domain: auth token
#         :return:
#         """
#         # We are testing 401 here. so campaign and blast ids will not matter.
#         unauthorize_test('post',  URL, 'invalid_token')
#
#     def test_associate_device_with_invalid_data(self, token_first):
#         """
#         Try to associate a device with invalid data, expecting 400 status code
#         :param token_first:
#         :return:
#         """
#         invalid_data_test('post', URL, token_first)
#
#     # Test URL: /v1/devices [POST]
#     def test_associate_device_with_invalid_candidate_id(self, token_first, candidate_first):
#         """
#         Try to associate a device to an invalid candidate id and it should
#         raise Invalid and ResourceNotFound error
#         :param token_first: auth token
#         :param candidate_first: candidate object
#         :return:
#         """
#         invalid_candiate_id = candidate_first['id'] + 10000
#         valid_device_id = PUSH_DEVICE_ID
#         invalid_candidate_data = {
#             '': (INVALID_USAGE, 'candidate_id is not given in post data'),
#             0: (INVALID_USAGE, 'candidate_id is not given in post data'),
#             -1: (NOT_FOUND, 'Unable to associate device with a non existing candidate id: -1'),
#             invalid_candiate_id: (NOT_FOUND, 'Unable to associate device with a non existing '
#                                              'candidate id: %s' % invalid_candiate_id)
#         }
#         for key in invalid_candidate_data:
#             data = dict(candidate_id=key, device_id=valid_device_id)
#             response = send_request('post', URL, token_first, data)
#             status_code, message = invalid_candidate_data[key]
#             assert response.status_code == status_code, 'exception raised'
#             error = response.json()['error']
#             assert error['message'] == message
#
#     def test_associate_device_with_invalid_device_id(self, token_first, candidate_first):
#         """
#         We will try to associate an invalid one signal device id to a valid candidate , we will get
#         InvalidUsage and ResourceNotFound error
#         :param token_first: auth token
#         :param candidate_first: candidate dict object
#         :return:
#         """
#         invalid_device_data = {
#                 '': (INVALID_USAGE, 'device_id is not given in post data'),
#                 0: (INVALID_USAGE, 'device_id is not given in post data'),
#                 'invalid_id': (NOT_FOUND, 'Device is not registered with OneSignal '
#                                           'with id invalid_id')
#             }
#         for key in invalid_device_data:
#             data = dict(candidate_id=candidate_first['id'], device_id=key)
#             response = send_request('post', URL, token_first, data)
#             status_code, message = invalid_device_data[key]
#             assert response.status_code == status_code, 'exception raised'
#             error = response.json()['error']
#             assert error['message'] == message
#
#     def test_associate_a_device_to_candidate(self, token_first, candidate_first):
#         """
#         We are associating a valid device id to a valid candidate and we are expecting 200 status code
#         :param token_first: auth token
#         :param candidate_first: candidate dict object
#         :return:
#         """
#         data = dict(candidate_id=candidate_first['id'], device_id=PUSH_DEVICE_ID)
#         response = send_request('post', URL, token_first, data)
#         assert response.status_code == OK, 'Could not associate device to candidate'
#
#         # A device has been associated to test_candidate through API but in tests
#         # we need to refresh our session to get those changes (using relationship)
#         # devices = candidate_first.devices.all()
#         response = send_request('get', CandidateApiUrl.DEVICES % candidate_first['id'], token_first)
#         assert response.status_code == OK
#         devices = response.json()['devices']
#
#         assert len(devices) == 1, 'One device should be associated to this test candidate'
#         device = devices[0]
#         assert device['one_signal_device_id'] == PUSH_DEVICE_ID