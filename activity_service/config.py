__author__ = 'erikfarmer'
import logging

import os

# Auth Server URI
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("activity_service.dev")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("activity_service.ci")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("activity_service.qa")
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    LOGGER = logging.getLogger("activity_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
