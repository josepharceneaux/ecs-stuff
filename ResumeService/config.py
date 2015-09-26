"""Application config file."""

__author__ = 'erikfarmer'

import os

# Auth Server URI
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    OAUTH_SERVER_URI = 'http://0.0.0.0:8081/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8000/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'https://www.gettalent-webdev.com/web/api/candidates.json'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    CANDIDATE_CREATION_URI = 'https://www.gettalent.com/web/api/candidates.json'
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = os.urandom(24).encode('hex')
