
"""Application config file."""

import os
import logging
import logging.config

__author__ = 'naveen'


# Load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
if GT_ENVIRONMENT == 'dev':
    OAUTH_SERVER_URI = 'http://127.0.0.1:8001/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8005/v1/candidates'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("candidate_service.dev")
    DEBUG = True
elif GT_ENVIRONMENT == 'circle':
    OAUTH_SERVER_URI = 'http://127.0.0.1:8001/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8005/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("candidate_service.ci")
    DEBUG = True
elif GT_ENVIRONMENT == 'qa':
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'https://webdev.gettalent.com/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("candidate_service.qa")
    DEBUG = False
elif GT_ENVIRONMENT == 'prod':
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'https://www.gettalent.com/web/api/candidates.json'
    LOGGER = logging.getLogger("candidate_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')

