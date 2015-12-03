"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

This contains following helper classes/functions for SMS Campaign Service.

- Class TwilioSMS which uses TwilioAPI to buy new number, or send sms etc.
- Function search_urls_in_text() to search a URL present in given text.
- Function url_conversion() which takes the URL and try to make it shorter using
    Google's shorten URL API.
"""

# Standard Library
import re
import json

# Third Party Imports
import twilio
import twilio.rest
from twilio.rest import TwilioRestClient

# Application Specific
from sms_campaign_service import logger
from sms_campaign_service.common.utils.common_functions import http_request
from sms_campaign_service.sms_campaign_app_constants import TWILIO_ACCOUNT_SID,\
    TWILIO_AUTH_TOKEN, GOOGLE_URL_SHORTENER_API_URL
from sms_campaign_service.custom_exceptions import TwilioAPIError, GoogleShortenUrlAPIError


class TwilioSMS(object):
    """
    This class contains the methods of Twilio API to be used for SMS campaign service
    """

    def __init__(self):
        self.client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.country = 'US'
        self.phone_type = 'local'
        self.sms_enabled = True
        # self.sms_call_back_url = 'http://demo.twilio.com/docs/sms.xml'
        self.sms_call_back_url = 'http://74cf4bd2.ngrok.io/sms_receive'
        self.sms_method = 'POST'

    def send_sms(self, body_text=None, receiver_phone=None, sender_phone=None):
        # -------------------------------------
        # sends SMS to given number
        # -------------------------------------
        try:
            message = self.client.messages.create(
                body=body_text,
                to=receiver_phone,
                from_=sender_phone
            )
            return message
        except twilio.TwilioRestException as error:
            raise TwilioAPIError(error_message=
                                 'Cannot get available number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)

    def get_available_numbers(self):
        # -------------------------------------
        # get list of available numbers
        # -------------------------------------
        try:
            phone_numbers = self.client.phone_numbers.search(
                country=self.country,
                type=self.phone_type,
                sms_enabled=self.sms_enabled,
            )
        except Exception as error:
            raise TwilioAPIError(error_message=
                                 'Cannot get available number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)
        return phone_numbers

    def purchase_twilio_number(self, phone_number):
        # --------------------------------------
        # Purchase a number
        # --------------------------------------
        try:
            number = self.client.phone_numbers.purchase(friendly_name=phone_number,
                                                        phone_number=phone_number,
                                                        sms_url=self.sms_call_back_url,
                                                        sms_method=self.sms_method,
                                                        )
            logger.info('Bought new Twilio number %s' % number.sid)
        except Exception as error:
            raise TwilioAPIError(error_message=
                                 'Cannot buy new number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)

    def update_sms_call_back_url(self, phone_number_sid):
        # --------------------------------------
        # Updates SMS callback URL of a number
        # --------------------------------------
        try:
            number = self.client.phone_numbers.update(phone_number_sid,
                                                      sms_url=self.sms_call_back_url)
            logger.info('SMS call back URL has been set to: %s' % number.sms_url)
        except Exception as error:
            raise TwilioAPIError(error_message=
                                 'Cannot buy new number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)

    def get_sid(self, phone_number):
        # --------------------------------------
        # Gets sid of a given number
        # --------------------------------------
        try:
            number = self.client.phone_numbers.list(phone_number=phone_number)
            if len(number) == 1:
                return 'SID of Phone Number %s is %s' % (phone_number, number[0].sid)
        except Exception as error:
            raise TwilioAPIError(error_message=
                                 'Cannot buy new number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)


def search_urls_in_text(text):
    """
    This checks if given text has any URL link present in it and returns all urls in a list.
    This checks for URLs starting with either http or https or www.
    :param text: string in which we want to search URL
    :type text: str
    :return: list of all URLs present in given text | []
    :rtype: list
    """
    return re.findall(r'https?://[^\s<>"]+|ftps?://[^\s<>"]+|www\.[^\s<>"]+', text)


def url_conversion(long_url):
    """
    We use Google's URL Shortener API to shorten the given URL.
    In this function we pass a URL which we want to shorten and on
    success it saves record in database and returns its id.
    :param long_url: The URL which we want to be shortened
    :type long_url: str
    :param long_url:
    :return: shortened URL
    :rtype: str
    """
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({'longUrl': long_url})
    response = http_request('POST', GOOGLE_URL_SHORTENER_API_URL, headers=headers, data=payload)
    data = response.json()
    if not data.has_key('error'):
        short_url = data['id']
        # long_url = data['longUrl']
        logger.info("url_conversion: Long URL was: %s" % long_url)
        logger.info("url_conversion: Shortened URL is: %s" % short_url)
        return short_url
    else:
        raise GoogleShortenUrlAPIError(error_message="Error while shortening URL. Long URL is %s"
                                       "Error dict is %s" % (long_url, data['error']['errors'][0]))
