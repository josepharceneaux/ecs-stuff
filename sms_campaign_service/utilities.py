__author__ = 'basit.gettalent@gmail.com'

# Standard Library
import re
import json
from datetime import datetime

# Third Party Imports
import twilio
import twilio.rest
from twilio.rest import TwilioRestClient

# Application Specific
from sms_campaign_service import logger
from sms_campaign_service.common.utils.common_functions import http_request
from sms_campaign_service.sms_campaign_app.app import sched
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, GOOGLE_URL_SHORTENER_API_URL
from sms_campaign_service.custom_exceptions import TwilioAPIError, GoogleShortenUrlAPIError

# from sms_campaign_service.app.app import celery


class TwilioSMS(object):
    """
    This class contains the methods of Twilio API to be used for sms campaign service
    """

    def __init__(self):
        self.client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.country = 'US'
        self.phone_type = 'local'
        self.sms_enabled = True
        self.sms_call_back_url = 'http://demo.twilio.com/docs/sms.xml'
        self.sms_method = 'POST'

    def send_sms(self, body_text=None, receiver_phone=None, sender_phone=None):
        # -------------------------------------
        # sends sms to given number
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
        # Updates SMS callback url of a number
        # --------------------------------------
        try:
            number = self.client.phone_numbers.update(phone_number_sid,
                                                      sms_url=self.sms_call_back_url)
            logger.info('SMS call back url has been set to: %s' % number.sms_url)
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


def search_link_in_text(text):
    return re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)


def url_conversion(long_url):
    """
    We use Google's URL Shortener API to shorten the given url.
    In this function we pass a url which we want to shorten and on
    success it saves record in database and returns its id.
    :param long_url: The url which we want to be shortened
    :type long_url: str
    :param long_url:
    :return: shortened url
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
        raise GoogleShortenUrlAPIError(error_message="Error while shortening URL. "
                                       "Error dict is %s" % data['error']['errors'][0])


def get_smart_list_ids():
    # TODO: get smart list ids from cloud service maybe
    return [1]


def run_func(arg1, arg2, end_date):
    if datetime.now().hour == end_date.hour \
            and datetime.now().minute == end_date.minute:
        stop_job(sched.get_jobs()[0])
    else:
        # send_sms_campaign.delay(arg1, arg2)
        pass


# @celery.task()
def run_func_1(func, args, end_date):
    # current_job = args[2]
    status = True
    for job in sched.get_jobs():
        if job.args[2] == end_date:
            if all([datetime.now().date() == end_date.date(),
                    datetime.now().hour == end_date.hour,
                    datetime.now().minute == end_date.minute]) \
                    or end_date < datetime.now():
                # job_status = 'Completed'
                stop_job(job)
                status = False
                # if status:
                # eval(func).delay(args[0], args[1])
    if status:
        # job_status = 'Running'
        func_1(args[0], args[1])
        # add_or_update_job_in_db(current_job, status=job_status)


def stop_job(job):
    sched.unschedule_job(job)
    print 'job(id: %s) has stopped' % job.id


# @celery.task()
# /sms_camp_service/scheduled_camp_process/
def func_1(a, b):
    print a, '\n', b


# @celery.task()
def func_2(a, b):
    print 'func_2'
