__author__ = 'ufarooqi'

import os
import logging
import logging.config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# SQL ALCHEMY DB URL
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("auth_service.dev")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("auth_service.ci")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("auth_service.qa")
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    LOGGER = logging.getLogger("auth_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 7200  # 2 hours expiry time for bearer token
