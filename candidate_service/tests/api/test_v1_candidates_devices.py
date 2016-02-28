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

from candidate_service.common.tests.conftest import *
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.modules.contsants import PUSH_DEVICE_ID
from candidate_service.tests.api.helpers import define_and_send_request, AddUserRoles


def test_associate_device_with_invalid_token(candidate_first):
    # TODO All great tests. kindly comment all methods albeit briefly
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    response = define_and_send_request('invalid_token', 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 401


def test_associate_device_to_non_existing_candidate(access_token_first):
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    candidate_id = sys.maxint
    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_id, data)
    logger.info(response.content)
    assert response.status_code == 404


def test_associate_device_with_invalid_one_signal_device_id(access_token_first, candidate_first):
    data = {
        'one_signal_device_id': 'Invalid Id'
    }
    response = define_and_send_request(access_token_first, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 404


def test_associate_device_to_deleted_candidate(access_token_first, user_first, candidate_first):
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


def test_associate_device_using_diff_user_token_same_domain(access_token_same, candidate_first):
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
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }

    response = define_and_send_request(access_token_second, 'post',
                                       CandidateApiUrl.DEVICES % candidate_first.id, data)
    logger.info(response.content)
    assert response.status_code == 403
