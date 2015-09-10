__author__ = 'erikfarmer'

import os

# Auth Server URI
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
