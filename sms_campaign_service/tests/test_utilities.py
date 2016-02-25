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
from sms_campaign_service.sms_campaign_app import app
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.modules.validators import (validate_url_by_http_request,
                                                     validate_url_format)
from sms_campaign_service.modules.custom_exceptions import (SmsCampaignApiException,
                                                            TwilioApiError)
from sms_campaign_service.modules.handy_functions import search_urls_in_text, TwilioSMS
from sms_campaign_service.modules.sms_campaign_app_constants import (TWILIO_TEST_NUMBER,
                                                                     TWILIO_INVALID_TEST_NUMBER)

# Common Utils
from sms_campaign_service.common.models.user import User
from sms_campaign_service.common.tests.conftest import fake
from sms_campaign_service.common.routes import (LOCAL_HOST, SmsCampaignApi, HEALTH_CHECK)
from sms_campaign_service.common.utils.handy_functions import url_conversion
from sms_campaign_service.common.error_handling import InvalidUsage, ResourceNotFound
from sms_campaign_service.common.campaign_services.tests_helpers import (get_invalid_ids,
                                                                         CampaignsTestsHelpers)


# Test for healthcheck
def test_health_check():
    response = requests.get(SmsCampaignApi.HOST_NAME % HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(SmsCampaignApi.HOST_NAME % HEALTH_CHECK + '/')
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
    invalid_url=fake.word())


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
        except InvalidUsage as error:
            assert error.status_code == SmsCampaignApiException.INVALID_URL_FORMAT


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
        except InvalidUsage as error:
            assert error.message, 'Invalid usage error should be raised'

    def test_with_invalid_url(self):
        """
        This tests url_conversion() with invalid URL. It should get None response and a
        error message.
        """
        with app.app_context():
            response, error = url_conversion(LOCAL_HOST)
            assert not response
            assert error


class TestTwilioSMS(object):
    """
    This class contains tests for TwilioSMS class defined in modules/handy_functions.py
    """

    def test_sms_send_with_valid_data(self):
        """
        Sending SMS from valid phone number to valid phone number
        :return:
        """
        response = self._send_sms(TWILIO_TEST_NUMBER, TWILIO_TEST_NUMBER)
        assert getattr(response, 'date_created')

    def test_sms_send_to_invalid_phone(self):
        """
        Sending SMS to invalid phone number
        :return:
        """
        try:
            self._send_sms(TWILIO_TEST_NUMBER, TWILIO_INVALID_TEST_NUMBER)
            assert None, \
                'Custom exception TwilioApiError should be thrown that receiver phone is invalid'
        except TwilioApiError as error:
            assert error.message

    def test_sms_send_from_invalid_phone(self):
        """
        Sending SMS from invalid phone number
        :return:
        """
        try:
            self._send_sms(TWILIO_TEST_NUMBER, TWILIO_INVALID_TEST_NUMBER)
            assert None, \
                'Custom exception TwilioApiError should be thrown that sender phone is invalid'
        except TwilioApiError as error:
            assert error.message

    def test_purchase_valid_number(self):
        """
        Purchasing valid phone number
        :return:
        """
        response = self._purchase_number(TWILIO_TEST_NUMBER), 'Purchasing valid number should ' \
                                                              'not raise any error'
        assert response

    def test_purchase_invalid_number(self):
        """
        Purchasing invalid phone number
        :return:
        """
        try:
            self._purchase_number(TWILIO_INVALID_TEST_NUMBER)
            assert None, \
                'Custom exception TwilioApiError should be thrown that phone number is invalid'
        except TwilioApiError as error:
            assert error.message

    def _send_sms(self, sender, receiver):
        twilio_obj = TwilioSMS()
        return twilio_obj.send_sms(fake.word(), sender, receiver)

    def _purchase_number(self, phone_number):
        twilio_obj = TwilioSMS()
        return twilio_obj.purchase_twilio_number(phone_number)


class TestTSmsCampaignBase(object):
    """
    This class contains tests for TwilioSMS class defined in modules/handy_functions.py
    """

    def test_creating_obj_with_non_existing_user_id(self):
        """
        Creating object of SmsCampaignBase class with non-existing user_ids.
        :return:
        """
        last_campaign_id_in_db = CampaignsTestsHelpers.get_last_id(User)
        ids = get_invalid_ids(last_campaign_id_in_db)
        error_message = None
        for _id in ids:
            try:
                SmsCampaignBase(_id)
                assert None, 'ResourceNotFound should be thrown as user_id does not exists in db.'
            except InvalidUsage as error:
                error_message = error.message
            except ResourceNotFound as error:
                error_message = error.message
            assert str(_id) in error_message

    def test_creating_obj_with_invalid_user_id(self):
        """
        Creating object of SmsCampaignBase class with invalid user_id.
        :return:
        """
        try:
            SmsCampaignBase(fake.word())
            assert None, 'ResourceNotFound should be thrown as user_id must be int|long.'
        except InvalidUsage as error:
            assert error.message
