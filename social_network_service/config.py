__author__ = 'zohaib'

import os
import logging
import logging.config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# SQL ALCHEMY DB URL
GT_ENVIRONMENT = os.getenv('GT_ENVIRONMENT') or 'dev'
if GT_ENVIRONMENT == 'dev':
    APP_URL = 'http://0.0.0.0:8006'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("social_network_service.dev")
    DEBUG = True
elif GT_ENVIRONMENT == 'jenkins':
    APP_URL = 'http://0.0.0.0:8006'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("social_network_service.ci")
    DEBUG = True
elif GT_ENVIRONMENT == 'qa':
    APP_URL = 'http://0.0.0.0:8006'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("social_network_service.qa")
    DEBUG = False
elif GT_ENVIRONMENT == 'prod':
    APP_URL = 'http://0.0.0.0:8006'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    LOGGER = logging.getLogger("social_network_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.getenv('SECRET_KEY')
OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 7200  # 2 hours expiry time for bearer token

# Meetup Credentials
MEETUP_ACCESS_TOKEN = 'b0060461e2a5b3f364744160bcccf754'
MEETUP_REFRESH_TOKEN = 'f938d5104470553b106bff54fdc998ce'

# Eventbrite Credentials
EVENTBRITE_ACCESS_TOKEN = '4DPJ5DXTTFKSG23ZANZT'
EVENTBRITE_REFRESH_TOKEN = ''
