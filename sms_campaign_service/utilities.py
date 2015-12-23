"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This contains following helper classes/functions for SMS Campaign Service.

- Class TwilioSMS which uses Twilio API to buy new number, or send SMS etc.
- Function search_urls_in_text() to search a URL present in given text.
- Function url_conversion() which takes the URL and try to make it shorter using
    Google's shorten URL API.
"""

# Standard Library
import re

# Third Party Imports
import twilio
import twilio.rest
from twilio.rest import TwilioRestClient

# Common Utils
from sms_campaign_service.common.routes import (SmsCampaignApiUrl, GTApis)
from sms_campaign_service.common.error_handling import (InvalidUsage, ResourceNotFound,
                                                        ForbiddenError)
from sms_campaign_service.common.utils.common_functions import (find_missing_items,
                                                                is_iso_8601_format,
                                                                JSON_CONTENT_TYPE_HEADER)

# Database Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.smart_list import SmartList
from sms_campaign_service.common.models.sms_campaign import SmsCampaign

# Application Specific
from sms_campaign_service import logger
from sms_campaign_service.custom_exceptions import (TwilioAPIError, MissingRequiredField,
                                                    InvalidDatetime, ErrorDeletingSMSCampaign)
from sms_campaign_service.sms_campaign_app_constants import (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
                                                             NGROK_URL)


class TwilioSMS(object):
    """
    This class contains the methods of Twilio API to be used for SMS campaign service
    """

    def __init__(self):
        self.client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.country = 'US'
        self.phone_type = 'local'
        self.sms_enabled = True

        # default value of sms_call_back_url is 'http://demo.twilio.com/docs/sms.xml'
        # TODO: Until app is up, will use ngrok address
        # self.sms_call_back_url = SmsCampaignApiUrl.RECEIVE_URL
        self.sms_call_back_url = NGROK_URL % SmsCampaignApiUrl.RECEIVE
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
    return re.findall(r'(?:http|ftp)s?://[^\s<>"]+|www\.[^\s<>"]+', text)


# TODO: remove this when app is up
def replace_ngrok_link_with_localhost(temp_ngrok_link):
    """
    We have exposed our endpoint via ngrok. We need to expose endpoint as Google's shorten URL API
    looks for valid URL to convert into shorter version. While making HTTP request to this endpoint,
    if ngrok is not running somehow, we replace that link with localhost to hit that endpoint. i.e.

        https://9a99a454.ngrok.io/v1/campaigns/1298/redirect/294/?candidate_id=544
    will become
        https://127.0.0.1:8011/v1/campaigns/1298/redirect/294/?candidate_id=544

    In final version of app, this won't be necessary as we'll have valid URL for app.
    :param temp_ngrok_link:
    :return:
    """
    relative_url = temp_ngrok_link.split(NGROK_URL % '')[1]
    # HOST_NAME is http://127.0.0.1:8011 for dev
    return SmsCampaignApiUrl.HOST_NAME % relative_url


# TODO: remove this when app is up
def replace_localhost_with_ngrok(localhost_url):
    """
    We have exposed our endpoint via ngrok. We need to expose endpoint as Google's shorten URL API
    looks for valid URL to convert into shorter version. While making HTTP request to this endpoint,
    if ngrok is not running somehow, we replace localhost_url with the ngrok exposed URL. i.e.

        https://127.0.0.1:8011/v1/campaigns/1298/redirect/294/?candidate_id=544

    will become

        https://9a99a454.ngrok.io/v1/campaigns/1298/redirect/294/?candidate_id=544


    In final version of app, this won't be necessary as we'll have valid URL for app.
    :param localhost_url:
    :return:
    """
    relative_url = localhost_url.split(str(GTApis.SMS_CAMPAIGN_SERVICE_PORT))[1]
    return NGROK_URL % relative_url


def validate_form_data(form_data):
    """
    This does the validation of the data received to create SMS campaign.

        1- If any key from (name, body_text, smartlist_ids) is missing from form data or
            has no value we raise MissingRequiredFieldError.
        2- If smartlist_ids are not present in database, we raise ResourceNotFound exception.
        3- If start_datetime or end_datetime is not valid datetime format, then we raise
            InvalidDatetime

    :param form_data:
    :return: list of ids of smartlists which were not found in database.
    :rtype: list
    """
    required_fields = ['name', 'body_text', 'smartlist_ids']
    # find if any required key is missing from data
    missing_fields = filter(lambda required_key: required_key not in form_data, required_fields)
    if missing_fields:
        raise MissingRequiredField('Required fields not provided to save sms_campaign. '
                                   'Missing fields are %s' % missing_fields)
    # find if any required key has no value
    missing_field_values = find_missing_items(form_data, required_fields)
    if missing_field_values:
        raise MissingRequiredField(
            error_message='Required fields are empty to save '
                          'sms_campaign. Empty fields are %s' % missing_field_values)
    # validate smartlist ids are in a list
    if not isinstance(form_data.get('smartlist_ids'), list):
        raise InvalidUsage(error_message='Include smartlist id(s) in a list.')

    not_found_smartlist_ids = []
    invalid_smartlist_ids = []
    for smartlist_id in form_data.get('smartlist_ids'):
        try:
            if not isinstance(smartlist_id, (int, long)):
                invalid_smartlist_ids.append(smartlist_id)
                raise InvalidUsage('Include smartlist id as int|long')
            if not SmartList.get_by_id(smartlist_id):
                not_found_smartlist_ids.append(smartlist_id)
                raise ResourceNotFound('Smartlist(id:%s) not found in database.' % smartlist_id)
        except InvalidUsage:
            logger.exception('validate_form_data: Invalid smartlist id')
        except ResourceNotFound:
            logger.exception('validate_form_data:')
    # If all provided smartlist ids are invalid, raise InvalidUsage
    if len(form_data.get('smartlist_ids')) == len(invalid_smartlist_ids):
        raise InvalidUsage(
            error_message='smartlists(id(s):%s are invalid. Valid id must be int|long'
                          % form_data.get('smartlist_ids'))
    # If all provided smartlist ids do not exist in database, raise ResourceNotFound
    if len(form_data.get('smartlist_ids')) == len(not_found_smartlist_ids):
        raise ResourceNotFound(error_message='smartlists(id(s):%s not found in database.'
                                             % form_data.get('smartlist_ids'))
    # filter out unknown smartlist ids, and keeping the valid ones
    form_data['smartlist_ids'] = list(set(form_data.get('smartlist_ids')) -
                                      set(invalid_smartlist_ids + not_found_smartlist_ids))
    for datetime in [form_data.get('send_datetime'), form_data.get('stop_datetime')]:
        if not is_iso_8601_format(datetime):
            raise InvalidDatetime('Invalid DateTime: Kindly specify UTC datetime in ISO-8601 '
                                  'format like 2015-10-08T06:16:55Z. Given Date is %s' % datetime)
    return invalid_smartlist_ids, not_found_smartlist_ids


def delete_sms_campaign(campaign_id, current_user_id):
    """
    This function is used to delete SMS campaign of a user. If current user is the
    creator of given campaign id, it will delete the campaign, otherwise it will
    raise the Forbidden error.
    :param campaign_id: id of SMS campaign to be deleted
    :param current_user_id: id of current user
    :exception: Forbidden error (status_code = 403)
    :exception: Resource not found error (status_code = 404)
    :exception: ErrorDeletingSMSCampaign
    :exception: InvalidUsage
    :return: True if record deleted successfully, False otherwise.
    :rtype: bool
    """
    if not isinstance(campaign_id, (int, long)):
        raise InvalidUsage(error_message='Include campaign_id as int|long')
    if is_owner_of_campaign(campaign_id, current_user_id):
        deleted = SmsCampaign.delete(campaign_id)
        if not deleted:
            raise ErrorDeletingSMSCampaign("Campaign(id:%s) couldn't be deleted."
                                           % campaign_id)
    return False


def is_owner_of_campaign(campaign_id, current_user_id):
    """
    This function returns True if the current user is an owner for given
    campaign_id. Otherwise it raises the Forbidden error.
    :param campaign_id: id of campaign form getTalent database
    :param current_user_id: Id of current user
    :exception: InvalidUsage
    :exception: ResourceNotFound
    :exception: ForbiddenError
    :return: True if current user is an owner for given campaign, False otherwise
    :rtype: bool
    """
    if not isinstance(campaign_id, (int, long)):
        raise InvalidUsage(error_message='Include campaign_id as int|long')
    campaign_obj = SmsCampaign.get_by_id(campaign_id)
    if not campaign_obj:
        raise ResourceNotFound(error_message='SMS Campaign(id=%s) not found.' % campaign_id)
    campaign_user_id = UserPhone.get_by_id(campaign_obj.user_phone_id).user_id
    if campaign_user_id == current_user_id:
        return True
    else:
        raise ForbiddenError(error_message='You are not the owner of '
                                           'SMS campaign(id:%s)' % campaign_id)


def validate_header(request):
    """
    Proper header should be {'content-type': 'application/json'} for POSTing
    some data on SMS campaign API.
    If header of request is not proper, it raises InvalidUsage exception
    :return:
    """
    if not request.headers.get('CONTENT_TYPE') == JSON_CONTENT_TYPE_HEADER['content-type']:
        raise InvalidUsage(error_message='Invalid header provided')
