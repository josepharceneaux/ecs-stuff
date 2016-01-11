"""Application config file."""

import os
import logging
import logging.config

__author__ = 'erikfarmer'

# Load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, '../logging.conf')
logging.config.fileConfig(LOGGING_CONF)

GT_ENVIRONMENT = os.getenv('GT_ENVIRONMENT') or 'dev'
if GT_ENVIRONMENT == 'dev':
    BATCH_PROCESSING_URI = 'http://127.0.0.1:8003/v1/batch/'
    BG_URL = 'http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8005/v1/candidates'
    DEBUG = True
    LOGGER = logging.getLogger("resume_service.dev")
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    SCHEDULER_SERVICE_URI = 'http://127.0.0.1:8011/v1/tasks'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
elif GT_ENVIRONMENT == 'circle':
    BATCH_PROCESSING_URI = 'http://127.0.0.1:8003/v1/batch/'
    BG_URL = 'http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8005/v1/candidates'
    DEBUG = True
    LOGGER = logging.getLogger("resume_service.ci")
    SCHEDULER_SERVICE_URI = 'http://127.0.0.1:8011/v1/tasks'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
elif GT_ENVIRONMENT == 'qa':
    BG_URL = 'http://sandbox-lensapi.burning-glass.com/v1.7/parserservice/resume'
    CANDIDATE_CREATION_URI = 'https://candidate-service-webdev.gettalent.com/v1/candidates'
    DEBUG = False
    LOGGER = logging.getLogger("resume_service.qa")
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
elif GT_ENVIRONMENT == 'prod':
    CANDIDATE_CREATION_URI = 'https://candidate-service.gettalent.com/v1/candidates'
    DEBUG = False
    LOGGER = logging.getLogger("resume_service.prod")
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.getenv('SECRET_KEY')
