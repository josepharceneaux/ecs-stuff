__author__ = 'erikfarmer'
import os

# Auth Server URI
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    ENVIRONMENT = 'dev'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8005/v1/candidates'
    OAUTH_ROOT = 'http://0.0.0.0:8001%s'
    OAUTH_AUTHORIZE_URI = OAUTH_ROOT % '/oauth2/authorize'
    OAUTH_TOKEN_URI = OAUTH_ROOT % '/oauth2/token'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    ENVIRONMENT = 'circle'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    ENVIRONMENT = 'qa'
    CANDIDATE_CREATION_URI = 'https://webdev.gettalent.com/web/api/candidates.json'
    OAUTH_ROOT = 'https://secure-webdev.gettalent.com%s'
    OAUTH_AUTHORIZE_URI = OAUTH_ROOT % '/oauth2/authorize'
    OAUTH_TOKEN_URI = OAUTH_ROOT % '/oauth2/token'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    ENVIRONMENT = 'prod'
    OAUTH_ROOT = 'https://secure.gettalent.com%s'
    OAUTH_AUTHORIZE_URI = OAUTH_ROOT % '/oauth2/authorize'
    OAUTH_TOKEN_URI = OAUTH_ROOT % '/oauth2/token'
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

ENCRYPTION_KEY = 'heylookeveryonewegotasupersecretkeyoverhere'
SECRET_KEY = os.urandom(24).encode('hex')
