# import pytest
# from candidate_service.candidate_app import app
# from candidate_service.candidate_app import db
# from candidate_service.common.tests.conftest import candidate_first
#
# from candidate_service.common.models.candidate import CandidateDevice
# from candidate_service.common.test_config_manager import load_test_config
#
#
# test_config = load_test_config()
# PUSH_DEVICE_ID = test_config['PUSH_CONFIG']['device_id_1']
#
#
# @pytest.fixture()
# def associate_device(request, candidate_first):
#     """
#     This fixture is being used to associate a device with candidate.
#     :param request:
#     :return:
#     """
#     device = CandidateDevice(one_signal_device_id=PUSH_DEVICE_ID,
#                              candidate_id=candidate_first.id)
#     db.session.add(device)
#     db.session.commit()
#
#     def tear_down():
#         CandidateDevice.query.filter_by(candidate_id=candidate_first.id,
#                                         one_signal_device_id=PUSH_DEVICE_ID).delete()
#
#     request.addfinalizer(tear_down)
#     return device
#
#
# @pytest.fixture()
# def delete_device(request):
#     """
#     This fixture is being used to delete device association with candidate at the end of a test.
#     It is because, if a one_signal_device_id is already associated to a candidate in same domain
#     then it can not be assigned to another candidate. So we are deleting this entry before next test.
#     :param request:
#     :return:
#     """
#     # this data dict will be modified at the end of test.
#     data = {}
#
#     def tear_down():
#         if 'device_id' in data and 'candidate_id' in data:
#             device_id = data['device_id']
#             candidate_id = data['candidate_id']
#             CandidateDevice.query.filter_by(one_signal_device_id=device_id,
#                                             candidate_id=candidate_id).delete()
#
#     request.addfinalizer(tear_down)
#     return data