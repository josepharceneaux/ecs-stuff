"""
This module contains pyTest for utility functions of SMS Campaign Service
"""
# Third Party Import
import requests

# Service Specific
from sms_campaign_service.utilities import search_urls_in_text
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl


def test_search_url_in_text():
    """
    In this test, we will verify that search_urls_in_text() function finds the links
    accurately in the given string.
    :return:
    """
    # test empty string
    test_string = ''
    assert len(search_urls_in_text(test_string)) == 0
    # test string with no link
    test_string = 'Dear candidates, your application has been received'
    assert len(search_urls_in_text(test_string)) == 0
    # test of http URL
    test_string = 'Dear candidates, please apply at http://www.example.com'
    assert len(search_urls_in_text(test_string)) == 1
    # test of https URL
    test_string = 'Dear candidates, please apply at https://www.example.com'
    assert len(search_urls_in_text(test_string)) == 1
    # test of www URL
    test_string = 'Dear candidates, please apply at www.example.com'
    assert len(search_urls_in_text(test_string)) == 1
    # test for multiple URLs
    test_string = 'Dear candidates, please apply at http://www.example.com' \
                  ' or www.example.com' \
                  ' or https://www.example.com'
    assert len(search_urls_in_text(test_string)) == 3
    # test of ftp URL
    test_string = 'Dear candidates, please download registration form at ftp://mysite.com ' \
                  'or ftps://mysite.com'
    assert len(search_urls_in_text(test_string)) == 2


def test_health_check():
    response = requests.get(SmsCampaignApiUrl.HOST_NAME + 'healthcheck')
    assert response.status_code == 200
