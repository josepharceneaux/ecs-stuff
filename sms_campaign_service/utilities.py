from common.models.candidate import CandidatePhone

__author__ = 'basit'

# Standard Library
import json

# Application Specific
from config import GOOGLE_API_KEY
from config import GOOGLE_URLSHORTENER_API_URL
from social_network_service.utilities import http_request


def url_conversion(long_url):
    """
    We use Google's URL Shortener API to shorten the given url.
    In this function we pass a url which we want to shorten and on
    success it returns short_url and long_url.
    :param long_url: The url which we want to be shortened
    :type long_url: str
    :param long_url:
    :return: short_url, long_url
    :rtype: tuple
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

# from pyshorteners import Shortener
# url = 'https://webdev.gettalent.com/web/user/login?_next=/web/default/angular#!/'
# # url = 'http://www.google.com'
# shortener = Shortener('TinyurlShortener')
# print "My short url is {}".format(shortener.short(url))


import twilio
import twilio.rest

# Application Specific
from config import TWILIO_ACCOUNT_SID
from config import TWILIO_AUTH_TOKEN
from config import TWILIO_NUMBER


def send_sms():
    data = None
    try:
        ids = get_smart_list_ids()
        for _id in ids:
            candidate_phone = CandidatePhone.get_by_candidate_id(_id)
            client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body="Hello World",
                to=str(candidate_phone.value),
                from_=TWILIO_NUMBER
            )
            data = {'message': 'SMS has been sent successfully to %s candidate(s)'
                               ' from %s. Body text is %s.' 
                               % (len(ids), message.from_, message.body),
                    'status_code': 200}
    except twilio.TwilioRestException as e:
        data = {'message': e.message,
                'status_code': 500}
    return data


def get_smart_list_ids():
    return [86]