"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for SMS campaign service.
"""
# Standard Imports

# Service Specific
from sms_campaign_service.modules.custom_exceptions import InvalidUrl

# Common stuff
from sms_campaign_service.common.utils.handy_functions import http_request
from sms_campaign_service.modules.handy_functions import search_urls_in_text
from sms_campaign_service.common.campaign_services.validators import is_valid_url_format


def validate_url_format(url):
    """
    This validates if given URL is valid or not
    :param url: URL to be validate
    :type url: str
    :exception: InvalidUrl if URL is in improper format
    :return:
    """
    if not is_valid_url_format(url):
        raise InvalidUrl('Given URL (%s) is not valid.' % url)
    return True


def validate_url_by_http_request(url):
    """
    This function makes HTTP GET call to given URL, and return True if we get OK response,
    It returns False otherwise
    :param url:
    :return: True or False
    :rtype: bool
    """
    try:
        http_request('GET', url)
    except Exception:
        return False
    return True


def validate_urls_in_body_text(text):
    """
    This function validates the URLs present in SMS body text. It first check if they
    are in valid format, then it makes HTTP GET call to that URL to verify the URL is live.
    :param text:
    :return:
    """
    urls = search_urls_in_text(text)
    invalid_urls = []
    for url in urls:
        try:
            validate_url_format(url)
            validate_url_by_http_request(url)
        except Exception:
            invalid_urls.append(url)
    return invalid_urls
