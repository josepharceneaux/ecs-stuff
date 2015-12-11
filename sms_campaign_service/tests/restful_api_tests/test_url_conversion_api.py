"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /url_conversion of URL conversion API.
"""

# Third Party Imports
import requests

# Application Specific
from sms_campaign_service.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (MethodNotAllowed, UnauthorizedError,
                                                        InvalidUsage, InternalServerError)

class TestUrlConversionAPI:
    """
    This class contains the tests for the endpoint /url_conversion
    """

    def test_get_with_invalid_token(self):
        """
        With invalid access token, should get unauthorized
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.URL_CONVERSION,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'
        assert 'short_url' not in response.json()

    def test_get_with_valid_token_and_no_data(self, auth_token):
        """
        Making GET call on endpoint with no data, should get Bad request error.
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.URL_CONVERSION,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be Bad request (400)'

    def test_get_with_valid_token_and_valid_data(self, auth_token):
        """
        Making GET call on endpoint with valid data,should get ok response.
        :param auth_token:
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.URL_CONVERSION,
                                headers=dict(Authorization='Bearer %s' % auth_token),
                                data={
                                    "long_url": 'https://webdev.gettalent.com/web/default/angular#!/'}
                                )
        assert response.status_code == 200, 'Status should be Bad request (400)'
        assert 'short_url' in response.json()

    def test_get_with_valid_token_and_invalid_data(self, auth_token):
        """
        Making GET call on endpoint with invalid data, should get internal server error.
        Error code should be 5004 (custom exception for Google's Shorten URL API Error)
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.URL_CONVERSION,
                                headers=dict(Authorization='Bearer %s' % auth_token),
                                data={"long_url": SmsCampaignApiUrl.API_URL}
                                )
        assert response.status_code == InternalServerError.http_status_code(), \
            'Status should be (500)'
        # custom exception for Google's Shorten URL API Error
        assert response.json()['error']['code'] == SmsCampaignApiException.GOOGLE_SHORTEN_URL_API_ERROR

    def test_for_post_request(self, auth_token):
        """
        POST method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.URL_CONVERSION,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == MethodNotAllowed.http_status_code(), \
            'POST method should not be allowed (405)'

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
