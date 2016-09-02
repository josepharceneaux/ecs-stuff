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
import requests

from candidate_service.candidate_app import logger
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request
from candidate_service.common.tests.api_conftest import *

test_config = load_test_config()
PUSH_DEVICE_ID = test_config['PUSH_CONFIG']['device_id_1']


def test_associate_device_with_invalid_token(candidate_first):
    """
    Try to associate a valid device id to valid candidate but with invalid token, API should
    raise Unauthorized (401) error.
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], 'invalid_token', data)
    logger.info(response.content)
    assert response.status_code == requests.codes.UNAUTHORIZED


def test_associate_device_to_non_existing_candidate(token_first):
    """
    Try to associate a valid device id to a non-existing candidate.
    API should raise ResourceNotFound (404) error.
    :param token_first: authentication token
    :return:
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    candidate_id = sys.maxint
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_id, token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_associate_device_with_invalid_one_signal_device_id(token_first, candidate_first):
    """
    Try to associate an invalid one signal device id to a valid candidate. API should raise
    ResourceNotFound (404) error.
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    """
    data = {'one_signal_device_id': 'Invalid Id'}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_associate_device_to_deleted_candidate(token_first, candidate_first):
    """
    Try to associate a valid device id to a deleted (web-hidden) candidate.
    API should raise ResourceNotFound (404) error.
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    """

    response = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_first['id'], token_first)
    logger.info(response.content)
    assert response.status_code == requests.codes.NO_CONTENT

    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_associate_device_with_valid_data(token_first, candidate_first):
    """
    Try to associate a valid device id to a valid candidate.
    API should assign that device id to candidate in CandidateDevice table and return a success
    response (201).
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.CREATED

    response = send_request('get', CandidateApiUrl.DEVICES % candidate_first['id'], token_first)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK
    response = response.json()
    assert 'devices' in response
    assert len(response['devices']) == 1


def test_associate_device_to_two_candidate_in_same_domain(token_first, candidate_first,
                                                          candidate_same_domain):
    """
    Try to associate a valid device id to a valid candidate.
    API should assign that device id to candidate in CandidateDevice table and return a success
    response (201).
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_same_domain['id'], token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.CREATED

    response = send_request('post', CandidateApiUrl.DEVICES % candidate_same_domain['id'], token_first, data)
    logger.info(response.content)
    # api raises invalid usage in production if we want to associate same device id to multiple candidates
    # but in dev or jenkins, this restriction is not applicable.
    # assert response.status_code == 400
    assert response.status_code == requests.codes.CREATED


def test_associate_device_using_diff_user_token_same_domain(token_same_domain, candidate_first):
    """
    Try to associate  a device to a candidate but authentication token belongs to a different
    user that is not owner of candidate but he is from same domain as owner user.
    We are expecting a success response (201).
    :param token_same_domain: authentication token
    :param candidate_first: candidate dict object
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], token_same_domain, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.CREATED

    response = send_request('get', CandidateApiUrl.DEVICES % candidate_first['id'], token_same_domain)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK
    response = response.json()
    assert 'devices' in response
    assert len(response['devices']) == 1


def test_associate_device_using_diff_user_token_diff_domain(token_second, candidate_first):
    """
    Try to associate  a device to a candidate but authentication token belongs to a different
    user that is not owner of candidate and he is from different domain.
    We are expecting a Forbidden response (403).
    :param token_second: authentication token
    :param candidate_first: candidate dict object
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], token_second, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.FORBIDDEN


def test_delete_candidate_device(token_first, candidate_first, candidate_device_first):
    """
    Sending a DELETE request to /v1/candidates/:id/devices will remove candidate association with push device.
    Expected status is 200
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    :param candidate_device_first: candidate push device
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first['id'], token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK


def test_delete_candidate_device_in_same_domain(token_same_domain, candidate_first, candidate_device_first):
    """
    In this test we will try to remove push device of a candidate from a user token that is in same domain
    but not the owner. We will get 200 response.
    :param token_same_domain: authentication token
    :param candidate_first: candidate dict object
    :param candidate_device_first: candidate push device
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first['id'], token_same_domain, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.OK


def test_delete_candidate_device_in_diff_domain(token_second, candidate_first, candidate_device_first):
    """
    In this test we will try to remove push device of a candidate from a user token that is from different domain
    and he is not the owner of candidate. We will get 403 response.
    :param token_second: authentication token
    :param candidate_first: candidate dict object
    :param candidate_device_first: candidate push device
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first['id'], token_second, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.FORBIDDEN


def test_delete_candidate_device_with_invalid_one_signal_id(token_first, candidate_first,
                                                            candidate_device_first):
    """
    In this test we will try to remove push device with invalid one signal device id that does not exist.
    We will get 404 response.
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    :param candidate_device_first: candidate push device
    """
    data = {'one_signal_device_id': 'Invalid Id'}
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_first['id'], token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND


def test_delete_candidate_device_with_invalid_candidate_id(token_first, candidate_device_first):
    """
    In this test we will try to remove push device of a candidate that does not exists. API will raise 404.
    :param token_first: authentication token
    :param candidate_device_first: candidate push device
    """
    data = {'one_signal_device_id': PUSH_DEVICE_ID}
    candidate_id = sys.maxint
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_id, token_first, data)
    logger.info(response.content)
    assert response.status_code == requests.codes.NOT_FOUND
