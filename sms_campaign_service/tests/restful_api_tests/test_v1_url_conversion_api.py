"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/url_conversion of URL conversion API.
"""

# Third Party Imports
import json
import requests

# Service Specific
from sms_campaign_service.custom_exceptions import SmsCampaignApiException

# Common Utils
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl, LOCAL_HOST
from sms_campaign_service.common.error_handling import (MethodNotAllowed, UnauthorizedError,
                                                        InvalidUsage, InternalServerError)


class TestUrlConversionAPI(object):
    """
    This class contains the tests for the endpoint /v1/url_conversion
    """

    def test_post_with_invalid_token(self):
        """
        POST with invalid access token, should get Unauthorized.
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.URL_CONVERSION,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'
        assert 'short_url' not in response.json()

    def test_post_with_valid_token_and_no_data(self, auth_token):
        """
        Making POST call on endpoint with no data, should get Bad request error.
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.URL_CONVERSION,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be Bad request (400)'

    def test_post_with_valid_header_and_valid_data(self, valid_header):
        """
        Making POST call on endpoint with valid data,should get ok response.
        :param valid_header:
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.URL_CONVERSION,
                                 headers=valid_header,
                                 data=
                                 json.dumps(
                                     {"url": 'https://webdev.gettalent.com/web/default/angular#!/'}
                                     ))
        assert response.status_code == 200, 'response should be ok'
        assert 'short_url' in response.json()

    def test_post_with_valid_header_and_invalid_data(self, valid_header):
        """
        Making POST call on endpoint with invalid data, should get internal server error.
        Error code should be 5004 (custom exception for Google's Shorten URL API Error)
        :param valid_header: authorization header for sample user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.URL_CONVERSION,
                                 headers=valid_header,
                                 data=json.dumps(
                                     {"url": LOCAL_HOST}
                                     ))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Status should be (500)'
        # custom exception for Google's Shorten URL API Error
        assert response.json()['error']['code'] == \
               SmsCampaignApiException.GOOGLE_SHORTEN_URL_API_ERROR

    def test_for_get_request(self, auth_token):
        """
        POST method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.URL_CONVERSION,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == MethodNotAllowed.http_status_code(), \
            'GET method should not be allowed (405)'

    def test_for_delete_request(self, auth_token):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.URL_CONVERSION,
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == MethodNotAllowed.http_status_code(), \
            'DELETE method should not be allowed (405)'
