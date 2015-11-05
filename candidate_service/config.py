import os
import logging
import logging.config

# Load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# SQLAlchemy DB URL
GT_ENVIRONMENT = os.environ.get('GT_ENVIRONMENT')
if GT_ENVIRONMENT == 'dev':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8001/oauth2/authorize'
    LOGGER = logging.getLogger('candidate_service.dev')
    DEBUG = True
elif GT_ENVIRONMENT == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    OAUTH_SERVER_URI = 'http://0.0.0.0:8001/oauth2/authorize'
    LOGGER = logging.getLogger('candidate_service.ci')
    DEBUG = True
elif GT_ENVIRONMENT == 'qa':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    OAUTH_SERVER_URI = 'https://secure-webdev.gettalent.com/oauth2/authorize'
    LOGGER = logging.getLogger('candidate_service.qa')
    DEBUG = False
elif GT_ENVIRONMENT == 'prod':
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    OAUTH_SERVER_URI = 'https://secure.gettalent.com/oauth2/authorize'
    LOGGER = logging.getLogger('candidate_service.prod')
    DEBUG = False
else:
    raise Exception('Environment variable GT_ENVIRONMENT not set correctly - could not run app.')
