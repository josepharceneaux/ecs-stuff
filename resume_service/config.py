"""Application config file."""
import logging
import os

__author__ = 'erikfarmer'


if os.environ.get('GT_ENVIRONMENT') == 'dev':
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8000/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("resume_service.dev")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8000/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("resume_service.ci")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'https://www.gettalent-webdev.com/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("resume_service.qa")
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'https://www.gettalent.com/web/api/candidates.json'
    LOGGER = logging.getLogger("resume_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
