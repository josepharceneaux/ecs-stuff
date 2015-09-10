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
    LOGGER = logging.getLogger("auth_service.web_dev")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
     # CircleCI provides circle_test as default configured db.
    SQLALCHEMY_DATABASE_URI = 'mysql://ubuntu@localhost/circle_test'
    LOGGER = logging.getLogger("auth_service.web_ci")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("auth_service.web_qa")
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    LOGGER = logging.getLogger("auth_service.web_prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
