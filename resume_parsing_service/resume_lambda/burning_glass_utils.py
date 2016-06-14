from OauthLib import OAuthClient
import HTMLParser
import requests
import urllib2

def fetch_optic_response(encoded_resume):
    oauth = OAuthClient(url='http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume',
                        method='POST', consumerKey='osman',
                        consumerSecret='aRFKEc3AJdR9zogE@M9Sis%QjZPxA5Oy',
                        token='Utility',
                        tokenSecret='Q5JuWpaMLUi=yveieiNKNWxqqOvHLNJ$',
                        signatureMethod='HMAC-SHA1',
                        oauthVersion='1.0')
    AUTH = oauth.get_authorizationString()
    HEADERS = {
        'accept': 'application/xml',
        'content-type': 'application/json',
        'Authorization': AUTH,
    }
    DATA = {
        'binaryData': encoded_resume,
        'instanceType': 'TM',
        'locale': 'en_us'
    }

    r = requests.post('http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume',
                      headers=HEADERS, json=DATA)
    html_parser = HTMLParser.HTMLParser()
    unquoted = urllib2.unquote(r.content).decode('utf8')
    unescaped = html_parser.unescape(unquoted)
    return unescaped