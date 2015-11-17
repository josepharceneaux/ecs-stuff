__author__ = 'basit'

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
from social_network_service.utilities import http_request
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.models.scheduler import SchedulerTask
from sms_campaign_service.common.models.candidate import CandidatePhone
from sms_campaign_service.app.app import celery
from sms_campaign_service.app.app import sched
from config import TWILIO_ACCOUNT_SID
from config import TWILIO_AUTH_TOKEN
from config import GOOGLE_API_KEY, REDIRECT_URL
from config import GOOGLE_URLSHORTENER_API_URL


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
        # print 'sms_sent'
        # return {'sent_time': datetime.now()}
        try:
            message = self.client.messages.create(
                body=body_text,
                to=receiver_phone,
                from_=sender_phone
            )
            return message
        except twilio.TwilioRestException as e:
            return {'message': e.message,
                    'status_code': 500}

    def get_available_numbers(self):
        # -------------------------------------
        # get list of available numbers
        # -------------------------------------
        phone_numbers = self.client.phone_numbers.search(
            country=self.country,
            type=self.phone_type,
            sms_enabled=self.sms_enabled,
        )
        return phone_numbers if phone_numbers else dict()

    def purchase_twilio_number(self, phone_number):
        # --------------------------------------
        # Purchase a number
        # --------------------------------------
        number = self.client.phone_numbers.purchase(friendly_name=phone_number,
                                                    phone_number=phone_number,
                                                    sms_url=self.sms_call_back_url,
                                                    sms_method=self.sms_method,
                                                    )
        print number.sid

    def update_sms_call_back_url(self, phone_number_sid):
        # --------------------------------------
        # Updates SMS callback url of a number
        # --------------------------------------
        number = self.client.phone_numbers.update(phone_number_sid,
                                                  sms_url=self.sms_call_back_url)
        print 'SMS call back url has been set to: %s' % number.sms_url

    def get_sid(self, phone_number):
        # --------------------------------------
        # Gets sid of a given number
        # --------------------------------------
        number = self.client.phone_numbers.list(phone_number=phone_number)
        if len(number) == 1:
            return 'SID of Phone Number %s is %s' % (phone_number, number[0].sid)

    # phone_number_sid = get_sid("+15039255479")
    # update_sms_call_back_url(phone_number_sid)
    # number_object = get_available_numbers()[0]
    # number_to_buy = number_object.phone_number
    # print number_to_buy
    # purchase_twilio_number(number_to_buy)


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
    :return: id of db record
    :rtype: int
    """
    url = GOOGLE_URLSHORTENER_API_URL + '?key=' + GOOGLE_API_KEY
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({'longUrl': long_url})
    response = http_request('POST', url, headers=headers, data=payload)
    try:
        data = response.json()
        short_url = data['id']
        long_url = data['longUrl']
        print "Long URL was: %s" % long_url
        print "Shortened URL is: %s" % short_url
        return short_url, long_url

    except Exception as e:
        print e.message


def process_redirection(url_conversion_id):
    """
    Gets the record from url_conversion db table using provided id.
    :param url_conversion_id: id of the record
    :type url_conversion_id: int
    :return: record from url_conversion
    :rtype: common.misc.UrlConversion
    """
    return UrlConversion.get_by_id(url_conversion_id)

# from pyshorteners import Shortener
# url = 'https://webdev.gettalent.com/web/user/login?_next=/web/default/angular#!/'
# # url = 'http://www.google.com'
# shortener = Shortener('TinyurlShortener')
# print "My short url is {}".format(shortener.short(url))


# @celery.task()
def send_sms_campaign(ids, body_text):
    """
    This function sends sms campaign
    :param ids: list of candidate ids to send sms campaign
    :type ids: list
    :param body_text:
    :type body_text: str
    :return:
    """
    # TODO: remove hard coded value
    user_phone = UserPhone.get_by_user_id(1)
    data = None
    try:
        for _id in ids:
            candidate_phone = CandidatePhone.get_by_candidate_id(_id)
            twilio_obj = TwilioSMS()
            result = twilio_obj.send_sms(receiver_phone=candidate_phone,
                                         sender_phone=user_phone,
                                         body_text=body_text)
            data = {'message': 'SMS has been sent successfully to %s candidate(s) '
                               'from %s. Body text is %s.'
                               % (len(ids), result.from_, result.body),
                    'status_code': 200}
    except twilio.TwilioRestException as e:
        data = {'message': e.message,
                'status_code': 500}
    return data


def get_smart_list_ids():
    # TODO: get smart list ids from cloud service maybe
    return [1]


def run_func(arg1, arg2, end_date):
    if datetime.now().hour == end_date.hour \
            and datetime.now().minute == end_date.minute:
        stop_job(sched.get_jobs()[0])
    else:
        send_sms_campaign.delay(arg1, arg2)


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


def get_all_tasks():
    tasks = SchedulerTask.query.all()
    return [task.to_json() for task in tasks]


# @celery.task()
# /sms_camp_service/scheduled_camp_process/
def func_1(a, b):
    print a, '\n', b


# @celery.task()
def func_2(a, b):
    print 'func_2'
