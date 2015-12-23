"""
This module contains pyTest for utility functions like

- search_url_in_text()
- url_conversion()
"""
# Third Party Imports
import requests

# Service Specific
from sms_campaign_service.tests.conftest import app
from sms_campaign_service.utilities import search_urls_in_text

# Common Utils
from sms_campaign_service.common.error_handling import InvalidUsage
from sms_campaign_service.common.utils.common_functions import url_conversion
from sms_campaign_service.common.routes import (SmsCampaignApiUrl, LOCAL_HOST)


# Test for healthcheck
def test_health_check():
    response = requests.get(SmsCampaignApiUrl.HOST_NAME % '/healthcheck')
    assert response.status_code == 200


class TestSearchUrlInText(object):
    """
    In this class, we will verify that search_urls_in_text() function finds the links
    accurately in the given string.
    """
    def test_with_empty_string(self):
        # test empty string
        test_string = ''
        assert len(search_urls_in_text(test_string)) == 0
        # test string with no link

    def test_with_no_url(self):
        test_string = 'Dear candidates, your application has been received'
        assert len(search_urls_in_text(test_string)) == 0
        # test string with valid URLs keywords like http, https, www.
        test_string = 'Dear candidates, as for http, we will use https. please visit at www'
        assert len(search_urls_in_text(test_string)) == 0

    def test_of_http_url(self):
        # test of http URL
        test_string = 'Dear candidates, please apply at http://www.example.com'
        test_result = search_urls_in_text(test_string)
        assert len(test_result) == 1
        assert test_result[0] in test_string

    def test_of_https_url(self):
        # test of https URL
        test_string = 'Dear candidates, please apply at https://www.example.com'
        test_result = search_urls_in_text(test_string)
        assert len(test_result) == 1
        assert test_result[0] in test_string

    def test_of_www_url(self):
        # test of www URL
        test_string = 'Dear candidates, please apply at www.example.com'
        test_result = search_urls_in_text(test_string)
        assert len(test_result) == 1
        assert test_result[0] in test_string

    def test_of_fttp_url(self):
        # test of ftp URL
        test_string = 'Dear candidates, please download registration form at ftp://mysite.com ' \
                      'or ftps://mysite.com'
        assert len(search_urls_in_text(test_string)) == 2
        test_result = search_urls_in_text(test_string)
        assert test_result[0] in test_string
        assert test_result[1] in test_string

    def test_of_multiple_urls(self):
        # test for multiple URLs
        test_string = 'Dear candidates, please apply at http://www.example.com' \
                      ' or www.example.com' \
                      ' or https://www.example.com'
        test_result = search_urls_in_text(test_string)
        assert len(test_result) == 3
        assert test_result[0] in test_string
        assert test_result[1] in test_string
        assert test_result[2] in test_string


class TestUrlConversion(object):
    """
    This class contains the tests for the common function url_conversion() defined in
    common_functions.py
    """

    def test_with_valid_param_type(self):
        """
        This tests url_conversion() with valid parameter type. i.e. str
        """
        with app.app_context():
            response, error = url_conversion('https://webdev.gettalent.com/web/default/angular#!/')
            assert not error
            assert response

    def test_with_invalid_param_type(self):
        """
        This tests url_conversion() with invalid parameter type. i.e. dict
        It should get InvalidUsage error.
        """
        try:
            url_conversion({"url":'https://webdev.gettalent.com/web/default/angular#!/'})
        except Exception as error:
            assert error.status_code == InvalidUsage.http_status_code(), \
                'Should be bad request(400)'

    def test_with_invalid_url(self):
        """
        This tests url_conversion() with invalid URL. It should get None response and a
        error message.
        """
        with app.app_context():
            response, error = url_conversion(LOCAL_HOST)
            assert not response
            assert error
