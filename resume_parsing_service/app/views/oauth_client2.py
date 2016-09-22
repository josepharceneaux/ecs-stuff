import binascii
import hashlib  # 2.5+
import hmac
import os
import time
import urllib2


HTTP_METHOD = 'POST'
OAUTH_SIGNATURE_METHOD = 'HMAC-SHA1'
OAUTH_TOKEN = 'Utility'
OAUTH_VERSION = '1.0'


def escape(s):
    """Escape a URL including any /."""
    return urllib2.quote(s, safe='~')


def generate_timestamp():
    """Return timestamp without decimals in string form."""
    return str(int(time.time()))


def generate_nonce():
    # See GET-1679
    return os.urandom(4).encode('hex')


def get_normalized_parameters(params):
    """Return a string that contains the parameters that must be signed."""
    key_values = [(escape(k), escape(v)) for k, v in params.iteritems()]
    key_values.sort() # REQUIRED
    return '&'.join(['{}={}'.format(k, v) for k, v in key_values])

def build_signature_base_string(url, consumer_secret, token_secret, parameters):
    sig = (
        escape(HTTP_METHOD),
        escape(url),
        escape(parameters),
    )
    key = '&'.join((escape(consumer_secret), escape(token_secret)))
    raw = '&'.join(sig)

    return key, raw

def build_signature(key, raw):
    """Builds the base signature string."""
    hashed = hmac.new(key, raw, hashlib.sha1)
    return binascii.b2a_base64(hashed.digest())[:-1]

def get_authorization_string(auth_params):
    OAUTH_TIMESTAMP = generate_timestamp()
    OAUTH_NONCE = generate_nonce()

    OAUTH_PARAMETERS = {
        'oauth_consumer_key': auth_params['consumer_key'],
        'oauth_token': OAUTH_TOKEN,
        'oauth_signature_method': OAUTH_SIGNATURE_METHOD,
        'oauth_timestamp': OAUTH_TIMESTAMP,
        'oauth_nonce': OAUTH_NONCE,
        'oauth_version': OAUTH_VERSION
    }

    normalized_params = get_normalized_parameters(OAUTH_PARAMETERS)
    key, raw = build_signature_base_string(auth_params['endpoint_url'], auth_params['consumer_secret'],
                                           auth_params['token_secret'], normalized_params)
    OAUTH_SIGNATURE = urllib2.quote(build_signature(key, raw))
    OAUTH_STRING = ("OAuth oauth_version=\"{}\", oauth_signature_method=\"{}\", "
                    "oauth_nonce=\"{}\", oauth_timestamp=\"{}\", oauth_consumer_key=\"{}\", "
                    "oauth_token=\"{}\", oauth_signature=\"{}\"")
    return OAUTH_STRING.format(OAUTH_VERSION, OAUTH_SIGNATURE_METHOD, OAUTH_NONCE,
                        OAUTH_TIMESTAMP, auth_params['consumer_key'], OAUTH_TOKEN, OAUTH_SIGNATURE)
