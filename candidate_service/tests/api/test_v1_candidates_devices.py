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
from candidate_service.tests.api.helpers import define_and_send_request, AddUserRoles

test_config = load_test_config()
PUSH_DEVICE_ID = test_config['PUSH_CONFIG']['device_id_1']


def test_associate_device_with_invalid_token(candidate_first):
    """
    Try to associate a valid device id to valid candidate but with invalid token, API should
    raise Unauthorized (401) error.
    :param candidate_first:
    :return:
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    response = define_and_send_request('invalid_token', 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 401


def test_associate_device_to_non_existing_candidate(access_token_first):
    """
    Try to associate a valid device id to a non-existing candidate.
    API should raise ResourceNotFound (404) error.
    :param access_token_first: authentication token
    :return:
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    candidate_id = sys.maxint
    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_id, data)
    logger.info(response.content)
    assert response.status_code == 404


def test_associate_device_with_invalid_one_signal_device_id(access_token_first, candidate_first):
    """
    Try to associate an invalid one signal device id to a valid candidate. API should raise
    ResourceNotFound (404) error.
    :param access_token_first: authentication token
    :param candidate_first: candidate dict object
    :return:
    """
    data = {
        'one_signal_device_id': 'Invalid Id'
    }
    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 404


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
    response = define_and_send_request(access_token_first, 'delete',
                                       CandidateApiUrl.CANDIDATE % candidate_first.id)
    logger.info(response.content)
    assert response.status_code == 204
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }

    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 404


def test_associate_device_with_valid_data(access_token_first, candidate_first):
    """
    Try to associate a valid device id to a valid candidate.
    API should assign that device id to candidate in CandidateDevice table and return a success
    response (201).
    :param access_token_first:
    :param candidate_first:
    :return:
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }

    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 201

    response = define_and_send_request(access_token_first, 'get',
                                       CandidateApiUrl.DEVICES % candidate_first.id)
    logger.info(response.content)
    assert response.status_code == 200
    response = response.json()
    assert 'devices' in response
    assert len(response['devices']) == 1


def test_associate_device_to_two_candidate_in_same_domain(access_token_first, candidate_first,
                                                          candidate_second):
    """
    Try to associate a valid device id to a valid candidate.
    API should assign that device id to candidate in CandidateDevice table and return a success
    response (201).
    :param access_token_first:
    :param candidate_first:
    :return:
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }

    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 201

    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_second.id, data)
    logger.info(response.content)
    assert response.status_code == 400


def test_associate_device_using_diff_user_token_same_domain(access_token_same, candidate_first):
    """
    Try to associate  a device to a candidate but authentication token belongs to a different
    user that is not owner of candidate but he is from same domain as owner user.
    We are expecting a success response (201).
    :param access_token_same:
    :param candidate_first:
    :return:
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }

    response = define_and_send_request(access_token_same, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 201

    response = define_and_send_request(access_token_same, 'get',
                                       CandidateApiUrl.DEVICES % candidate_first.id)
    logger.info(response.content)
    assert response.status_code == 200
    response = response.json()
    assert 'devices' in response
    assert len(response['devices']) == 1


def test_associate_device_using_diff_user_token_diff_domain(access_token_second, candidate_first):
    """
    Try to associate  a device to a candidate but authentication token belongs to a different
    user that is not owner of candidate and he is from different domain.
    We are expecting a Forbidden response (403).
    :param access_token_second:
    :param candidate_first:
    :return:
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }

    response = define_and_send_request(access_token_second, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 403
