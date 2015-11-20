__author__ = 'basit'

import os
import logging
import logging.config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# SQL ALCHEMY DB URL
GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
if GT_ENVIRONMENT == 'dev':
    APP_URL = 'http://0.0.0.0:8007'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("social_network_service.dev")
elif GT_ENVIRONMENT == 'circle':
    APP_URL = 'http://0.0.0.0:5000'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("social_network_service.ci")
elif GT_ENVIRONMENT == 'qa':
    APP_URL = 'http://0.0.0.0:5000'
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("social_network_service.qa")
elif GT_ENVIRONMENT == 'prod':
    APP_URL = 'http://0.0.0.0:5000'
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    LOGGER = logging.getLogger("social_network_service.prod")
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")
if LOGGER:
    LOGGER.info("sms_campaign_service is running in %s environment"
                % GT_ENVIRONMENT)

GOOGLE_API_KEY = 'AIzaSyCT7Gg3zfB0yXaBXSPNVhFCZRJzu9WHo4o'
GOOGLE_URL_SHORTENER_API_URL = 'https://www.googleapis.com/urlshortener/v1/url?key=' \
                               + GOOGLE_API_KEY

TWILIO_ACCOUNT_SID = "AC7f332b44c4a2d893d34e6b340dbbf73f"
TWILIO_AUTH_TOKEN = "09e1a6e40b9d6588f8a6050dea6bbd98"
SMS_URL_REDIRECT = 'http://2ed87e65.ngrok.io/sms_campaign/{}/url_redirection/{}/'
CAMPAIGN_SEND = 6
CAMPAIGN_SMS_SEND = 24
CAMPAIGN_SMS_CLICK = 25
PHONE_LABEL_ID = 1
ACTIVITY_SERVICE_API_URL = 'http://127.0.0.1:8002'
AUTH_HEADER = {'Authorization': 'Bearer gulqrgtuucodxdrijqwy'}
TWILIO = 'Twilio'
POOL_SIZE = 5

