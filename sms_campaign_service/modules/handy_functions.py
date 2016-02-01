"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This contains following helper classes/functions for SMS Campaign Service.

- Class TwilioSMS which uses Twilio API to buy new number, or send SMS etc.
- Function search_urls_in_text() to search a URL present in given text.

"""
# Standard Imports
import re

# Third Party Imports
import twilio
import twilio.rest
from twilio.rest import TwilioRestClient


# Service specific
from sms_campaign_service.common.utils.validators import format_phone_number
from sms_campaign_service.sms_campaign_app import flask_app, logger, app
from sms_campaign_service.modules.custom_exceptions import TwilioApiError
from sms_campaign_service.modules.sms_campaign_app_constants import NGROK_URL, TWILIO_TEST_NUMBER

# Common utils
from sms_campaign_service.common.talent_config_manager import TalentConfigKeys
from sms_campaign_service.common.error_handling import (InvalidUsage, ResourceNotFound,
                                                        ForbiddenError)
from sms_campaign_service.common.routes import (GTApis, SmsCampaignApi)
from sms_campaign_service.common.campaign_services.campaign_utils import \
    raise_if_dict_values_are_not_int_or_long
from sms_campaign_service.common.utils.handy_functions import raise_if_not_instance_of

# Database models
from sms_campaign_service.common.models.sms_campaign import SmsCampaignBlast


class TwilioSMS(object):
    """
    This class contains the methods of Twilio API to be used for SMS campaign service
    """

    def __init__(self):
        if flask_app.config[TalentConfigKeys.IS_DEV]:
            # This client is created using test_credentials of Twilio
            self.client = twilio.rest.TwilioRestClient(
                app.config[TalentConfigKeys.TWILIO_TEST_ACCOUNT_SID],
                app.config[TalentConfigKeys.TWILIO_TEST_AUTH_TOKEN]
            )
        else:
            # This client has actual app credentials of Twilio
            self.client = twilio.rest.TwilioRestClient(
                app.config[TalentConfigKeys.TWILIO_ACCOUNT_SID],
                app.config[TalentConfigKeys.TWILIO_AUTH_TOKEN]
            )
        self.country = 'US'
        self.phone_type = 'local'
        self.sms_enabled = True
        # default value of sms_call_back_url is 'http://demo.twilio.com/docs/sms.xml'
        # TODO: Until app is up, will use ngrok address
        # self.sms_call_back_url = SmsCampaignApi.RECEIVE
        self.sms_call_back_url = NGROK_URL % SmsCampaignApi.RECEIVE
        self.sms_method = 'POST'

    def validate_a_number(self, phone_number):
        """
        This method is used to validate a given phone number.
        :param phone_number: phone number
        :type phone_number: basestring
        """
        raise_if_not_instance_of(phone_number, basestring)
        try:
            # This does not work with Test Credentials
            response = self.client.caller_ids.validate(phone_number)
            return response
        except twilio.TwilioRestException as error:
            logger.error('Cannot validate given number. Error is "%s"'
                         % error.msg if hasattr(error, 'msg') else error.message)
        return False

    def send_sms(self, body_text, sender_phone, receiver_phone):
        """
        This method sends SMS from sender_phone to receiver_phone.
        :param body_text: body text to be sent in SMS
        :param sender_phone: phone number of sender
        :param receiver_phone: phone number of receiver
        :type body_text: basestring
        :type sender_phone: basestring
        :type receiver_phone: basestring
        """
        try:
            message = self.client.messages.create(
                body=body_text,
                to=receiver_phone,
                from_=sender_phone
            )
            if message.sid:
                return message
            else:
                raise TwilioApiError('sent SMS has no SID associated.')
        except twilio.TwilioRestException as error:
            raise TwilioApiError('Cannot send SMS. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)

    def get_available_numbers(self):
        """
        This method returns available numbers on Twilio API to be purchase.
        """
        try:
            phone_numbers = self.client.phone_numbers.search(
                country=self.country,
                type=self.phone_type,
                sms_enabled=self.sms_enabled,
            )
        except twilio.TwilioRestException as error:
            raise TwilioApiError('Cannot get available number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)
        return phone_numbers

    def purchase_twilio_number(self, phone_number):
        """
        This method purchases given phone number
        :param phone_number: phone number to be purchase
        :type phone_number: basestring
        """
        try:
            response = self.client.phone_numbers.purchase(friendly_name=phone_number,
                                                          phone_number=phone_number,
                                                          sms_url=self.sms_call_back_url,
                                                          sms_method=self.sms_method
                                                          )
            logger.info('Bought new Twilio number %s' % phone_number)
        except twilio.TwilioRestException as error:
            raise TwilioApiError('Cannot buy new number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)
        return response

    def update_sms_call_back_url(self, phone_number):
        """
        This method updates Callback URL for a particular Twilio number.
        :param phone_number: Given phone number
        :type phone_number: basestring
        """
        try:
            phone_number_sid = self.get_sid(phone_number)
            number = self.client.phone_numbers.update(phone_number_sid,
                                                      sms_url=self.sms_call_back_url)
            logger.info('SMS call back URL has been set to: %s' % number.sms_url)
        except twilio.TwilioRestException as error:
            raise TwilioApiError('Error updating callback URL. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)

    def get_sid(self, phone_number):
        """
        This returns the SID of a given Twilio number
        :param phone_number: phone number
        :type phone_number: basestring
        """
        try:
            number = self.client.phone_numbers.list(phone_number=phone_number)
            if len(number) == 1:
                return 'SID of Phone Number %s is %s' % (phone_number, number[0].sid)
        except twilio.TwilioRestException as error:
            raise TwilioApiError('Error getting SID of phone_number. Error is "%s"'
                                 % error.msg if hasattr(error, 'msg') else error.message)


# TODO: remove this when app is up
def replace_ngrok_link_with_localhost(temp_ngrok_link):
    """
    We have exposed our endpoint via ngrok. We need to expose endpoint as Google's shorten URL API
    looks for valid URL to convert into shorter version. While making HTTP request to this endpoint,
    if ngrok is not running somehow, we replace that link with localhost to hit that endpoint. i.e.

        https://9a99a454.ngrok.io/redirect/294
    will become
        https://127.0.0.1:8012/redirect/294

    In final version of app, this won't be necessary as we'll have valid URL for app.
    :param temp_ngrok_link:
    :return:
    """
    relative_url = temp_ngrok_link.split(NGROK_URL % '')[1]
    # HOST_NAME is http://127.0.0.1:8011 for dev
    return SmsCampaignApi.HOST_NAME % relative_url


# TODO: remove this when app is up
def replace_localhost_with_ngrok(localhost_url):
    """
    We have exposed our endpoint via ngrok. We need to expose endpoint as Google's shorten URL API
    looks for valid URL to convert into shorter version. While making HTTP request to this endpoint,
    if ngrok is not running somehow, we replace localhost_url with the ngrok exposed URL. i.e.

        https://127.0.0.1:8012/redirect/294

    will become

        https://9a99a454.ngrok.io/redirect/294

    In final version of app, this won't be necessary as we'll have valid URL for app.
    :param localhost_url:
    :return:
    """
    relative_url = localhost_url.split(str(GTApis.SMS_CAMPAIGN_SERVICE_PORT))[1]
    return NGROK_URL % relative_url


def search_urls_in_text(text):
    """
    This checks if given text has any URL link present in it and returns all urls in a list.
    This checks for URLs starting with either http or https or www.
    :param text: string in which we want to search URL
    :type text: str
    :return: list of all URLs present in given text | []
    :rtype: list
    """
    raise_if_not_instance_of(text, basestring)
    return re.findall(r'(?:http|ftp)s?://[^\s<>"]+|www\.[^\s<>"]+', text)


def request_from_google_shorten_url_api(requested_header):
    """
    When we use Google's shorten URL API, it hits the provided long_url.
    :param header_of_request:
    :
    :return:
    """
    keys = ['HTTP_FROM', 'HTTP_REFERER']
    for key in keys:
        if key in requested_header and 'google' in requested_header[key]:
            logger.info("Successfully verified by Google's shorten URL API")


def get_valid_blast_obj(blast_id, requested_campaign_id):
    """
    This gets the blast object from SmsCampaignBlast database table.
    If no object is found corresponding to given blast_id, it raises ResourceNotFound.
    If campaign_id associated with blast_obj is not same as the requested campaign id,
    we raise forbidden error.
    :param blast_id:
    :param requested_campaign_id:
    :type blast_id: int | long
    :type requested_campaign_id: int | long
    :exception: ResourceNotFound
    :exception: ForbiddenError
    :return: campaign blast object
    :rtype: SmsCampaignBlast
    """
    raise_if_dict_values_are_not_int_or_long(dict(campaign_id=requested_campaign_id,
                                                  blast_id=blast_id))
    blast_obj = SmsCampaignBlast.get_by_id(blast_id)
    if not blast_obj:
        raise ResourceNotFound("SMS campaign's Blast(id:%s) does not exists in database."
                               % blast_id)
    if not blast_obj.campaign_id == requested_campaign_id:
        raise ForbiddenError("SMS campaign's Blast(id:%s) is not associated with campaign(id:%s)."
                             % (blast_id, requested_campaign_id))
    return blast_obj


def get_formatted_phone_number(phone_number):
    """
    This function formats the given phone number using format_phone_number() defined in
    common/utils/validators.py
    :param phone_number:
    :return:
    """
    raise_if_not_instance_of(phone_number, basestring)
    try:
        formatted_phone_number = format_phone_number(phone_number)['formatted_number']
    except InvalidUsage:
        # Adding this condition here so that in tests, fake.phone_number()
        # does not always generate American/Canadian number, so format_phone_number()
        # throws Invalid usage error. In that case we assign Twilio's Test phone number.
        if not app.config[TalentConfigKeys.IS_DEV]:
            logger('get_formatted_phone_number: Given phone %s number is invalid.' % phone_number)
            raise
        formatted_phone_number = TWILIO_TEST_NUMBER
    return formatted_phone_number
