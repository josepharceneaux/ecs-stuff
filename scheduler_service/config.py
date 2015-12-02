__author__ = 'saad'

import os
import logging
import logging.config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)
os.environ['GT_ENVIRONMENT'] = 'dev'

# SQL ALCHEMY DB URL
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    APP_URL = 'http://0.0.0.0:8009'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8001/oauth2/authorize'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:fastian123@localhost/talent_local'
    LOGGER = logging.getLogger("scheduler_service.dev")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    APP_URL = 'http://0.0.0.0:5000'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8001/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("scheduler_service.ci")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    APP_URL = 'http://0.0.0.0:8009'
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("scheduler_service.qa")
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    APP_URL = 'http://0.0.0.0:8009'
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    LOGGER = logging.getLogger("scheduler_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")
if LOGGER:
    LOGGER.info("Scheduling Service is running in %s environment"
                % os.environ.get('GT_ENVIRONMENT'))