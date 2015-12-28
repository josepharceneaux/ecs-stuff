"""
This module contains pyTest for utility functions like

- search_url_in_text()
- url_conversion()
- validate_url_format()
- validate_url_by_http_request()
"""
# Third Party Imports
import requests

# Service Specific
from sms_campaign_service.tests.conftest import app
from sms_campaign_service.common.tests.conftest import fake
from sms_campaign_service.custom_exceptions import (InvalidUrl, SmsCampaignApiException)
from sms_campaign_service.utilities import (search_urls_in_text, validate_url_format,
                                            validate_url_by_http_request)

# Common Utils
from sms_campaign_service.common.error_handling import InvalidUsage
from sms_campaign_service.common.utils.common_functions import url_conversion
from sms_campaign_service.common.routes import (LOCAL_HOST, SmsCampaignApi)


# Test for healthcheck
def test_health_check():
    response = requests.get(SmsCampaignApi.HOST_NAME % '/healthcheck')
    assert response.status_code == 200


TEST_DATA = dict(
    no_url='Dear candidates, your application has been received',
    with_keywords='Dear candidates, as for http, we will use https. please visit at www',
    http_url='Dear candidates, please apply at http://www.example.com',
    https_url='Dear candidates, please apply at https://www.example.com',
    www_url='Dear candidates, please apply at www.example.com',
    ftp_url='Dear candidates, please download registration form at ftp://mysite.com '
            'or ftps://mysite.com',
    multiple_urls='Dear candidates, please apply at http://www.example.com or www.example.com '
                  'or https://www.example.com',
    valid_url='https://www.google.com',
    invalid_url=fake.words())


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
        # test with string having no URL
        assert len(search_urls_in_text(TEST_DATA['no_url'])) == 0

    def test_with_keywords(self):
        # test string with valid URLs keywords like http, https, www.
        assert len(search_urls_in_text(TEST_DATA['with_keywords'])) == 0

    def test_of_http_url(self):
        # test of http URL
        test_result = search_urls_in_text(TEST_DATA['http_url'])
        assert len(test_result) == 1
        assert test_result[0] in TEST_DATA['http_url']

    def test_of_https_url(self):
        # test of https URL
        test_result = search_urls_in_text(TEST_DATA['https_url'])
        assert len(test_result) == 1
        assert test_result[0] in TEST_DATA['https_url']

    def test_of_www_url(self):
        # test of www URL
        test_result = search_urls_in_text(TEST_DATA['www_url'])
        assert len(test_result) == 1
        assert test_result[0] in TEST_DATA['www_url']

    def test_of_ftp_url(self):
        # test of ftp URL
        test_result = search_urls_in_text(TEST_DATA['ftp_url'])
        assert len(test_result) == 2
        assert test_result[0] in TEST_DATA['ftp_url']
        assert test_result[1] in TEST_DATA['ftp_url']

    def test_of_multiple_urls(self):
        # test for multiple URLs
        test_result = search_urls_in_text(TEST_DATA['multiple_urls'])
        assert len(test_result) == 3
        assert test_result[0] in TEST_DATA['multiple_urls']
        assert test_result[1] in TEST_DATA['multiple_urls']
        assert test_result[2] in TEST_DATA['multiple_urls']


class TestValidUrlFormat(object):
    """
    In this class, we will verify that validate_url_format() function validates the given URL
    is in proper format.
    """

    def test_of_http_url(self):
        # test of http URL
        test_result = search_urls_in_text(TEST_DATA['http_url'])
        assert len(test_result) == 1
        self._assert_validate_url_format(test_result[0])

    def test_of_https_url(self):
        # test of https URL
        test_result = search_urls_in_text(TEST_DATA['https_url'])
        assert len(test_result) == 1
        self._assert_validate_url_format(test_result[0])

    def test_of_www_url(self):
        # test of www URL
        test_result = search_urls_in_text(TEST_DATA['www_url'])
        assert len(test_result) == 1
        self._assert_validate_url_format(test_result[0])

    def test_of_ftp_url(self):
        # test of ftp URL
        test_result = search_urls_in_text(TEST_DATA['ftp_url'])
        assert len(test_result) == 2
        self._assert_validate_url_format(test_result[0])
        self._assert_validate_url_format(test_result[1])

    def test_of_multiple_urls(self):
        # test for multiple URLs
        test_result = search_urls_in_text(TEST_DATA['multiple_urls'])
        assert len(test_result) == 3
        self._assert_validate_url_format(test_result[0])
        self._assert_validate_url_format(test_result[1])
        self._assert_validate_url_format(test_result[2])

    def _assert_validate_url_format(self, url):
        try:
            assert validate_url_format(url)
        except InvalidUrl as e:
            assert e.error_code == SmsCampaignApiException.INVALID_URL_FORMAT


class TestValidUrlByHTTPRequest(object):
    """
    This class contains tests for function validate_url_by_http_request.
    """

    def test_of_valid_url(self):
        # test for valid URL
        assert validate_url_by_http_request(TEST_DATA['valid_url'])

    def test_of_invalid_url(self):
        # test for invalid URL
        assert not validate_url_by_http_request(TEST_DATA['invalid_url'])


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
            response, error = url_conversion(TEST_DATA['valid_url'])
            assert not error
            assert response

    def test_with_invalid_param_type(self):
        """
        This tests url_conversion() with invalid parameter type. i.e. dict
        It should get InvalidUsage error.
        """
        try:
            url_conversion({"url": TEST_DATA['valid_url']})
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
