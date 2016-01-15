"""
This module contains tests code that is common across services. e.g SMS and Push campaign.
"""

__author__ = 'basit'

# Standard Imports
import json
from datetime import datetime

# Third Party
import requests

# Application Specific
from ..tests.conftest import fake
from ..utils.handy_functions import JSON_CONTENT_TYPE_HEADER
from ..error_handling import ForbiddenError, InvalidUsage, UnauthorizedError, ResourceNotFound


class CampaignsCommonTests(object):
    """
    This class contains common tests for sms_campaign_service and push_campaign_service.
    """

    @classmethod
    def schedule_with_put_method(cls, url, auth_token, data):
        """
        This function is for trying to schedule a campaign with PUT method.
        :param url:
        :param auth_token:
        :param data:
        :return:
        """
        response = send_request('put', url, auth_token, data)
        assert response.status_code == ForbiddenError.http_status_code()
        error = response.json()['error']
        assert error['message'] == 'Use POST method instead to schedule campaign first time'

    @classmethod
    def missing_fields_in_schedule_data(cls, method, url, token, data, one_time_job=True):
        # Test missing start_datetime field which is mandatory to schedule a campaign
        _assert_api_response_for_missing_field(method, url, token, data, 'start_datetime')
        if not one_time_job:  # if periodic job, need to test for end_datetime as well
            _assert_api_response_for_missing_field(method, url, token, data, 'end_datetime')

    @classmethod
    def invalid_datetime_format(cls, url, token, data):
        """
        Here we pass start_datetime and end_datetime in invalid format
        :param url:
        :param token:
        :param data:
        :return:
        """
        _assert_invalid_datetime_format(url, token, data, 'start_datetime')
        _assert_invalid_datetime_format(url, token, data, 'end_datetime')

    @classmethod
    def reschedule_with_invalid_token(cls, url, data):
        _assert_unauthorized('put', url, 'invalid_token', data)

    @classmethod
    def reschedule_with_invalid_data(cls, url, token):
        _invalid_data_test('put', url, token)

    @classmethod
    def reschedule_with_invalid_campaign_id(cls, url, token, data, last_campaign_id_in_db):
        # Test with invalid integer id
        # Test for 404, Schedule a campaign which does not exists or id is invalid
        invalid_ids = _get_invalid_ids(last_campaign_id_in_db)
        for _id, status_code in invalid_ids:
            response = send_request('put', url % _id, token, data)
            assert response.status_code == status_code
    
    @classmethod
    def reschedule_with_post_method(self, url, token, data):
        # Test forbidden error. To schedule a task first time, we have to send POST,
        # but we will send request using PUT which is for update and will validate error
        response = send_request('post', url, token, data)
        _assert_api_response(response, expected_status_code=ForbiddenError.http_status_code())


def send_request(method, url, access_token, data=None, is_json=True, data_dumps=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.test_reschedule_with_invalid_token
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = JSON_CONTENT_TYPE_HEADER['content-type']
    if data_dumps:
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


def get_fake_dict():
    """
    This method just creates a dictionary with 3 random keys and values

    : Example:

        data = {
                    'excepturi': 'qui',
                    'unde': 'ipsam',
                    'magni': 'voluptate'
                }
    :return: data
    :rtype dict
    """
    data = dict()
    for _ in range(3):
        data[fake.word()] = fake.word()
    return data


def get_invalid_fake_dict():
    """
    This method just creates a dictionary with 3 random keys and values

    : Example:

        data = {
                    'excepturi': 'qui',
                    'unde': 'ipsam',
                    'magni': 'voluptate'
                }
    :return: data
    :rtype dict
    """
    fake_dict = get_fake_dict()
    fake_dict[len(fake_dict.keys())-1] = [fake.word]
    return fake_dict


def _assert_api_response_for_missing_field(method, url, token, data, field_to_remove):
    """
    This function removes the field from data as specified by field_to_remove, and
    then POSTs data on given URL. It then asserts that removed filed is in error_message.
    :param method:
    :param url:
    :param token:
    :param data:
    :param field_to_remove:
    :return:
    """
    removed_value = data[field_to_remove]
    del data[field_to_remove]
    response = send_request(method, url, token, data)
    error = _assert_api_response(response)
    assert field_to_remove in error['message'], '%s should be in error_message' % field_to_remove
    # assign removed field again
    data[field_to_remove] = removed_value


def _assert_invalid_datetime_format(url, token, data, key):
    """
    Here we modify field of data as specified by param 'key' and then assert the invalid usage
    error in response of HTTP request.
    :param url:
    :param token:
    :param data:
    :param key:
    :return:
    """
    str_datetime = str(datetime.utcnow())
    old_value = data[key]
    data[key] = str_datetime  # Invalid datetime format
    response = send_request('post', url, token, data)
    _assert_api_response(response)
    data[key] = old_value


def _assert_unauthorized(method, url, access_token, data=None):
    """
    For a given URL, here we request with invalid token and assert that we get Unauthorized error.
    :param method:
    :param url:
    :param access_token:
    :param data:
    :return:
    """
    response = send_request(method, url, access_token, data)
    assert response.status_code == UnauthorizedError.http_status_code()


def _invalid_data_test(method, url, token):
    """
    This is used to make HTTP request as specified by 'method' on given URL and assert invalid
    usage error in response.
    :param method:
    :param url:
    :param token:
    :return:
    """
    # test with None Data
    data = None
    response = send_request(method, url, token, data)
    _assert_api_response(response)
    # Test with empty dict
    data = {}
    _assert_api_response(response)
    response = send_request(method, url, token, data)
    _assert_api_response(response)
    # Test with valid data and invalid header
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    _assert_api_response(response)
    # Test with Non JSON data and valid header
    data = get_invalid_fake_dict()
    response = send_request(method, url, token, data, data_dumps=False)
    _assert_api_response(response)


def _assert_api_response(response, expected_status_code=InvalidUsage.http_status_code()):
    """
    This method is used to assert Invalid usage error in given response
    :param response:
    :return:
    """
    assert response.status_code == expected_status_code
    error = response.json()['error']
    assert error, 'error key is missing from response'
    assert error['message']
    return error


def _get_invalid_ids(last_id_of_obj_in_db):
    """
    Given a database model object, here we create a list of two Invalid ids. One of them
    is 0 and other one is 100 plus the id of last record.
    """
    non_existing_id = last_id_of_obj_in_db + 100
    return [(0, InvalidUsage.http_status_code()),
            (non_existing_id, ResourceNotFound.http_status_code())]
