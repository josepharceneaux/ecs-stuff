import binascii
import hashlib  # 2.5+
import hmac
import os
import time
import urllib2


class OAuthClient:

    HTTP_METHOD = 'POST'
    OAUTH_SIGNATURE_METHOD = 'HMAC-SHA1'
    OAUTH_TOKEN = 'Utility'
    OAUTH_VERSION = '1.0'


    def __init__(self, url, consumerKey, consumerSecret, tokenSecret,):
        self.ENDPOINT_URL = url
        self.OAUTH_CONSUMER_KEY = consumerKey
        self.OAUTH_CONSUMER_SECRET = consumerSecret
        self.OAUTH_TOKEN_SECRET = tokenSecret


    def escape(self, s):
        """Escape a URL including any /."""
        return urllib2.quote(s, safe='~')


    def generate_timestamp(self):
        return str(int(time.time()))


    def generate_nonce(self):
        return os.urandom(4).encode('hex')


    def get_normalized_parameters(self):
        """Return a string that contains the parameters that must be signed."""
        params = self.OAUTH_PARAMETERS
        # Escape key values before sorting.
        key_values = [(self.escape(k), self.escape(v)) for k, v in params.iteritems()]

        key_values.sort() # REQUIRED
        # Combine key value pairs into a string.
        return '&'.join(['{}={}'.format(k, v) for k, v in key_values])


    def build_signature_base_string(self):
        sig = (
            self.escape(self.HTTP_METHOD),
            self.escape(self.ENDPOINT_URL),
            self.escape(self.get_normalized_parameters()),
        )

        key = '&'.join((self.escape(self.OAUTH_CONSUMER_SECRET), self.escape(self.OAUTH_TOKEN_SECRET)))
        raw = '&'.join(sig)
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

        OAUTH_SIGNATURE = urllib2.quote(self.build_signature())

        OAUTH_STRING = "OAuth oauth_version="+'"'+self.OAUTH_VERSION+'"'+", oauth_signature_method="+'"'+self.OAUTH_SIGNATURE_METHOD+'"'+", oauth_nonce="+'"'+OAUTH_NONCE+'"'+", oauth_timestamp="+'"'+str(OAUTH_TIMESTAMP)+'"'+", oauth_consumer_key="+'"'+self.OAUTH_CONSUMER_KEY+'"'+", oauth_token="+'"'+self.OAUTH_TOKEN+'"'+", oauth_signature="+'"'+OAUTH_SIGNATURE+'"'+""
        return OAUTH_STRING
