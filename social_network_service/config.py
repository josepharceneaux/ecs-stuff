__author__ = 'zohaib'

import os
import logging
import logging.config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# SQL ALCHEMY DB URL
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    APP_URL = 'http://0.0.0.0:8006'
    UI_APP_URL = 'http://localhost:3002/'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8001/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("social_network_service.dev")
    GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    APP_URL = 'http://0.0.0.0:8006'
    UI_APP_URL = 'http://localhost:3000/'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8001/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("social_network_service.ci")
    GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    APP_URL = 'http://0.0.0.0:8006'
    UI_APP_URL = 'http://localhost:3000/'  # TODO: change it to actual url
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("social_network_service.qa")
    GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    APP_URL = 'http://0.0.0.0:8006'
    UI_APP_URL = 'http://localhost:3000/'  # TODO: change it to actual url
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    LOGGER = logging.getLogger("social_network_service.prod")
    GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 7200  # 2 hours expiry time for bearer token

# Meetup Credentials
MEETUP_ACCESS_TOKEN = '25f8c0558af38af3410ca3b497c1a336'
MEETUP_REFRESH_TOKEN = 'cd03fe5b259735f588a93016b7894be6'

# Eventbrite Credentials
EVENTBRITE_ACCESS_TOKEN = '4DPJ5DXTTFKSG23ZANZT'
EVENTBRITE_REFRESH_TOKEN = ''
