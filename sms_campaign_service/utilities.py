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