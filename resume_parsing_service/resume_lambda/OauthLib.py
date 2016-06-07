import binascii
import hashlib  # 2.5+
import hmac
import random
import time
import urllib
import urlparse


class OAuthClient:

    HTTP_METHOD = 'GET'

    OAUTH_CONSUMER_KEY = ''
    OAUTH_CONSUMER_SECRET = ''
    OAUTH_TOKEN = 'token'
    OAUTH_TOKEN_SECRET = ''

    OAUTH_PARAMETERS = ''

    OAUTH_SIGNATURE_METHOD = 'HMAC-SHA1'
    OAUTH_VERSION = '1.0'
    ENDPOINT_URL = ''

    def __init__(self, url, method, consumerKey, consumerSecret, token, tokenSecret,
                 signatureMethod, oauthVersion):
        self.ENDPOINT_URL = url
        self.HTTP_METHOD = method
        self.OAUTH_CONSUMER_KEY = consumerKey
        self.OAUTH_CONSUMER_SECRET = consumerSecret
        self.OAUTH_TOKEN = token
        self.OAUTH_TOKEN_SECRET = tokenSecret
        self.OAUTH_SIGNATURE_METHOD = signatureMethod
        self.OAUTH_VERSION = oauthVersion

    def escape(self, s):
        """Escape a URL including any /."""
        return urllib.quote(s, safe='~')

    def _utf8_str(self, s):
        """Convert unicode to utf-8."""
        if isinstance(s, unicode):
            return s.encode("utf-8")
        else:
            return str(s)

    def generate_timestamp(self):
        return int(time.time())

    def generate_nonce(self, length=8):
        return ''.join([str(random.randint(0, 9)) for i in range(length)])

    def get_normalized_parameters(self):
        """Return a string that contains the parameters that must be signed."""
        params = self.parameters
        try:
            # Exclude the signature if it exists.
            del params['oauth_signature']
        except:
            pass
        # Escape key values before sorting.
        key_values = [(self.escape(self._utf8_str(k)), self.escape(self._utf8_str(v)))
                      for k, v in params.items()]
        # Sort lexicographically, first after key, then after value.
        key_values.sort()
        # Combine key value pairs into a string.
        return '&'.join(['%s=%s' % (k, v) for k, v in key_values])

    def get_normalized_http_method(self):
        """Uppercases the http method."""
        return self.HTTP_METHOD.upper()

    def get_normalized_http_url(self):
        """Parses the URL and rebuilds it to be scheme://host/path."""
        parts = urlparse.urlparse(self.ENDPOINT_URL)
        scheme, netloc, path = parts[:3]
        # Exclude default port numbers.
        if scheme == 'http' and netloc[-3:] == ':80':
            netloc = netloc[:-3]
        elif scheme == 'https' and netloc[-4:] == ':443':
            netloc = netloc[:-4]
        return '%s://%s%s' % (scheme, netloc, path)

    def get_normalized_parameters(self):
        """Return a string that contains the parameters that must be signed."""
        params = self.OAUTH_PARAMETERS
        urlparams = urlparse.urlparse(self.ENDPOINT_URL)
        # check for query string
        if(len(urlparams.query) > 0):
            params.update({urlparams.query.split("=")[0]: urlparams.query.split("=")[1]})
        try:
            # Exclude the signature if it exists.
            del params['oauth_signature']
        except:
            pass
        # Escape key values before sorting.
        key_values = [(self.escape(self._utf8_str(k)), self.escape(self._utf8_str(v)))
                      for k, v in params.items()]
        # Sort lexicographically, first after key, then after value.
        key_values.sort()
        # remove print
        # print '&'.join(['%s=%s' % (k, v) for k, v in key_values])
        # Combine key value pairs into a string.
        return '&'.join(['%s=%s' % (k, v) for k, v in key_values])

    def build_signature_base_string(self):
        sig = (
            self.escape(self.get_normalized_http_method()),
            self.escape(self.get_normalized_http_url()),
            self.escape(self.get_normalized_parameters()),
        )

        key = '%s&' % self.escape(self.OAUTH_CONSUMER_SECRET)
        if self.OAUTH_TOKEN_SECRET:
            key += self.escape(self.OAUTH_TOKEN_SECRET)
        raw = '&'.join(sig)
        # remove print
        # print raw
        return key, raw

    def build_signature(self):
        """Builds the base signature string."""
        key, raw = self.build_signature_base_string()

        # HMAC object.
        hashed = hmac.new(key, raw, hashlib.sha1)

        # Calculate the digest base 64.
        return binascii.b2a_base64(hashed.digest())[:-1]

    def get_authorizationString(self):
        OAUTH_TIMESTAMP = self.generate_timestamp()
        OAUTH_NONCE = self.generate_nonce()

        self.OAUTH_PARAMETERS = {
                                'oauth_consumer_key': self.OAUTH_CONSUMER_KEY,
                                'oauth_token': self.OAUTH_TOKEN,
                                'oauth_signature_method': self.OAUTH_SIGNATURE_METHOD,
                                'oauth_timestamp': OAUTH_TIMESTAMP,
                                'oauth_nonce': OAUTH_NONCE,
                                'oauth_version': self.OAUTH_VERSION
                            }

        OAUTH_SIGNATURE = urllib.quote(self.build_signature())

        # check this!
        self.OAUTH_PARAMETERS['oauth_signature'] = OAUTH_SIGNATURE

        OAUTH_STRING = "OAuth oauth_version="+'"'+self.OAUTH_VERSION+'"'+", oauth_signature_method="+'"'+self.OAUTH_SIGNATURE_METHOD+'"'+", oauth_nonce="+'"'+OAUTH_NONCE+'"'+", oauth_timestamp="+'"'+str(OAUTH_TIMESTAMP)+'"'+", oauth_consumer_key="+'"'+self.OAUTH_CONSUMER_KEY+'"'+", oauth_token="+'"'+self.OAUTH_TOKEN+'"'+", oauth_signature="+'"'+OAUTH_SIGNATURE+'"'+""
        return OAUTH_STRING
