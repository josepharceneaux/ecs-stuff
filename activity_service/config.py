__author__ = 'erikfarmer'
import os
import logging
import logging.config
from activity_service.common import talent_property_manager

# Load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)


GT_ENVIRONMENT = talent_property_manager.get_env()
if GT_ENVIRONMENT == 'dev':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("activity_service.dev")
    DEBUG = True
elif GT_ENVIRONMENT == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    LOGGER = logging.getLogger("activity_service.ci")
    DEBUG = True
elif GT_ENVIRONMENT == 'qa':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    LOGGER = logging.getLogger("activity_service.qa")
    DEBUG = False
elif GT_ENVIRONMENT == 'prod':
    LOGGER = logging.getLogger("activity_service.prod")
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

SECRET_KEY = talent_property_manager.get_secret_key()
