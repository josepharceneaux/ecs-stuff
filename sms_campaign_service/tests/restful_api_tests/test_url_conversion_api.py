"""
This module consists pyTests for URL conversion API.
"""

# Third Party Imports
import requests

# Application Specific
from sms_campaign_service import flask_app as app

APP_URL = app.config['APP_URL']
URL_CONVERSION_API_URL = APP_URL + '/url_conversion'


class TestUrlConversionAPI:

    def test_get_with_invalid_token(self):
        """
        With invalid access token, should get unauthorized
        :return:
        """
        response = requests.get(URL_CONVERSION_API_URL,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'
        assert 'short_url' not in response.json()

    def test_get_with_valid_token_and_no_data(self, auth_token):
        """
        Making GET call on endpoint with no data, should get Bad request error.
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.get(URL_CONVERSION_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 400, 'Status should be Bad request (400)'

    def test_get_with_valid_token_and_valid_data(self, auth_token):
        """
        Making GET call on endpoint with valid data,should get ok response.
        :param auth_token:
        :return:
        """
        response = requests.get(URL_CONVERSION_API_URL,
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
        response = requests.get(URL_CONVERSION_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token),
                                data={"long_url": APP_URL}
                                )
        assert response.status_code == 500, 'Status should be (500)'
        # custom exception for Google's Shorten URL API Error
        assert response.json()['error']['code'] == 5004

    def test_for_post_request(self, auth_token):
        """
        POST method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.post(URL_CONVERSION_API_URL,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 405, 'POST method should not be allowed (405)'

    def test_for_delete_request(self, auth_token):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :return:
        """
        response = requests.delete(URL_CONVERSION_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 405, 'DELETE method should not be allowed (405)'
