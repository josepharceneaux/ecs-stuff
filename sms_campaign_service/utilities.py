__author__ = 'basit'

# Standard Library
import json

# Application Specific
from config import GOOGLE_API_KEY, REDIRECT_URL
from config import GOOGLE_URLSHORTENER_API_URL
from social_network_service.utilities import http_request
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.models.candidate import CandidatePhone
from sms_campaign_service.common.models.user import UserPhone


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


def send_sms_campaign(ids, body_text):
    """
    This function sends sms campaign
    :param ids: list of candidate ids to send sms campaign
    :type ids: list
    :param body_text:
    :type body_text: str
    :return:
    """
    # TODO: remove hard codeed value
    user_phone = UserPhone.get_by_user_id(1)
    data = None
    try:
        for _id in ids:
            candidate_phone = CandidatePhone.get_by_candidate_id(_id)
            client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=body_text,
                to=candidate_phone.value,
                from_=user_phone.value
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
    # TODO: get smart list ids from cloud service maybe
    return [86]


def process_link_in_body_text(body_text):
    """
    - Once we have the body text of sms to be sent via sms campaign,
        we check if it contains any link in it.
        If it has any link, we do the followings:

            1- Save that link in db table "url_conversion".
            2- Checks if the db record has source url or not. If it has no source url,
               we convert the url(to redirect to our app) into shortened url and update
               the db record. Otherwise we move on to transform body text.
            3. Replace the link in original body text with the shortened url
                (which we created in step 2)
            4. Return the updated body text

        Otherwise we return the body text as it is
    :param body_text: body text to be sent via sms campaign containing any link.
    :type body_text: str
    :return: body text to be sent via sms campaign
    :rtype: str
    """
    link_in_body_text = get_url_in_body_text(body_text)
    if link_in_body_text:
        url_conversion_id = save_or_update_url_conversion(link_in_body_text)
        url_conversion_record = UrlConversion.get_by_id(url_conversion_id)
        if not url_conversion_record.source_url:
            short_url, long_url = url_conversion(REDIRECT_URL+'?url_id=%s' % url_conversion_id)
            save_or_update_url_conversion(link_in_body_text, source_url=short_url)
        else:
            short_url = url_conversion_record.source_url
        body_text = transform_body_text(body_text, short_url)
    return body_text


def get_url_in_body_text(body_text):
    """
    Here we get any link present in original body text
    :param body_text:
    :type body_text: str
    :return:
    """
    splited_text = body_text.split(' ')
    for word in splited_text:
        if 'www' in word or 'http' in word:
            return word
    return ''


def transform_body_text(body_text, short_url):
    """
    - This replaces the url provided in body text with the shortened url
        to be sent via sms campaign.
    :param body_text: body text to be sent in sms campaign
    :param short_url: shortened url
    :type body_text: str
    :type short_url: str
    :return: transformed body text to be sent via sms campaign
    :rtype: str
    """
    splited_text = body_text.split(' ')
    index = 0
    for word in splited_text:
        if 'www' in word or 'http' in word:
            splited_text[index] = short_url
            break
        index += 1
    return ' '.join(splited_text)


def save_or_update_url_conversion(link_in_body_text, source_url=None):
    """
    - Here we save the url(provided in body text) and the shortened url
        to redirect to our endpoint in db table "url_conversion".
    :param link_in_body_text: link present in body text
    :param source_url: shortened url of the link present in body text
    :type link_in_body_text: str
    :type source_url: str
    :return: id of the record in database
    :rtype: int
    """
    data = {'destination_url': link_in_body_text}
    data.update({'source_url': source_url}) if source_url else ''
    record_in_db = UrlConversion.get_by_destination_url(link_in_body_text)
    if record_in_db:
        record_in_db.update(**data)
        url_record_id = record_in_db.id
    else:
        new_record = UrlConversion(**data)
        UrlConversion.save(new_record)
        url_record_id = new_record.id
    return url_record_id


def process_redirection(url_conversion_id):
    """
    Gets the record from url_conversion db table using provided id.
    :param url_conversion_id: id of the record
    :type url_conversion_id: int
    :return: record from url_conversion
    :rtype: common.misc.UrlConversion
    """
    return UrlConversion.get_by_id(url_conversion_id)

