"""
This module contains test for API endpoint
        /v1/candidates/:id/devices
In these tests, we will try to associate OneSignal device id to candidates in
different scenarios like:
    - with invalid token
    - with invalid candidate id (non-existing)
    - with a deleted candidate id (web-hidden)
    - with valid candidate id but invalid OneSignalDevice id
    - with token for a different user from same domain
    - with token from a different user from different domain
"""
import sys

# this import is not used per se but without it, the test throws an app context error
# Candidate Service app instance
from candidate_service.candidate_app import app, logger
from candidate_service.common.test_config_manager import load_test_config
from candidate_service.common.tests.conftest import *
from candidate_service.common.routes import CandidateApiUrl
from helpers import AddUserRoles
from candidate_service.common.utils.test_utils import send_request

test_config = load_test_config()
PUSH_DEVICE_ID = test_config['PUSH_CONFIG']['device_id_1']


def test_associate_device_with_invalid_token(candidate_first):
    """
    Try to associate a valid device id to valid candidate but with invalid token, API should
    raise Unauthorized (401) error.
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, 'invalid_token', data)
    logger.info(response.content)
    assert response.status_code == 401


def test_associate_device_to_non_existing_candidate(access_token_first):
    """
    Try to associate a valid device id to a non-existing candidate.
    API should raise ResourceNotFound (404) error.
    :param access_token_first: authentication token
    :return:
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    candidate_id = sys.maxint
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_associate_device_with_invalid_one_signal_device_id(access_token_first, candidate_first):
    """
    Try to associate an invalid one signal device id to a valid candidate. API should raise
    ResourceNotFound (404) error.
    :param access_token_first: authentication token
    :param candidate_first: candidate dict object
    :return:
    """
    data = {'one_signal_device_id': 'Invalid Id'}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_associate_device_to_deleted_candidate(access_token_first, user_first, candidate_first):
    """
    Try to associate a valid device id to a deleted (web-hidden) candidate.
    API should raise ResourceNotFound (404) error.
    :param access_token_first:
    :param user_first:
    :param candidate_first:
    :return:
    """
    AddUserRoles.delete(user_first)
    response = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
    logger.info(response.content)
    assert response.status_code == requests.codes.NO_CONTENT

    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_associate_device_with_valid_data(access_token_first, candidate_first, delete_device):
    """
    Try to associate a valid device id to a valid candidate.
    API should assign that device id to candidate in CandidateDevice table and return a success
    response (201).
    :param access_token_first:
    :param candidate_first:
    :return:
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.CREATED

    response = send_request('get', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK
    response = response.json()
    assert 'devices' in response
    assert len(response['devices']) == 1

    # Set data to be used in finalizer to delete device association
    delete_device['candidate_id'] = candidate_first.id
    delete_device['device_id'] = PUSH_DEVICE_ID


def test_associate_device_to_two_candidate_in_same_domain(access_token_first, candidate_first,
                                                          candidate_second, delete_device):
    """
    Try to associate a valid device id to a valid candidate.
    API should assign that device id to candidate in CandidateDevice table and return a success
    response (201).
    :param access_token_first:
    :param candidate_first:
    :return:
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.CREATED

    response = send_request('post', CandidateApiUrl.DEVICES % candidate_second.id, access_token_first, data)
    logger.info(response.content)
    # api raises invalid usage in production if we want to associate same device id to multiple candidates
    # but in dev or jenkins, this restriction is not applicable.
    # assert response.status_code == 400
    assert response.status_code == requests.codes.CREATED

    # Set data to be used in finalizer to delete device association
    delete_device['candidate_id'] = candidate_first.id
    delete_device['device_id'] = PUSH_DEVICE_ID


def test_associate_device_using_diff_user_token_same_domain(access_token_same, candidate_first, delete_device):
    """
    Try to associate  a device to a candidate but authentication token belongs to a different
    user that is not owner of candidate but he is from same domain as owner user.
    We are expecting a success response (201).
    :param access_token_same:
    :param candidate_first:
    :return:
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, access_token_same, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.CREATED

    response = send_request('get', CandidateApiUrl.DEVICES % candidate_first.id, access_token_same)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK
    response = response.json()
    assert 'devices' in response
    assert len(response['devices']) == 1

    # Set data to be used in finalizer to delete device association
    delete_device['candidate_id'] = candidate_first.id
    delete_device['device_id'] = PUSH_DEVICE_ID


def test_associate_device_using_diff_user_token_diff_domain(access_token_second, candidate_first):
    """
    Try to associate  a device to a candidate but authentication token belongs to a different
    user that is not owner of candidate and he is from different domain.
    We are expecting a Forbidden response (403).
    :param access_token_second:
    :param candidate_first:
    :return:
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first.id, access_token_second, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.FORBIDDEN


def test_delete_candidate_device(access_token_first, candidate_first, associate_device):
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK


def test_delete_candidate_device_in_same_domain(access_token_same, candidate_first, associate_device):
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first.id, access_token_same, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK


def test_delete_candidate_device_in_diff_domain(access_token_second, candidate_first, associate_device):
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first.id, access_token_second, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.FORBIDDEN


def test_delete_candidate_device_with_invalid_one_signal_id(access_token_first, candidate_first, associate_device):
    data = {'one_signal_device_id': 'Invalid Id'}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first.id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_delete_candidate_device_with_invalid_candidate_id(access_token_first, associate_device):
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    candidate_id = sys.maxint
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_id, access_token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.FOUND
