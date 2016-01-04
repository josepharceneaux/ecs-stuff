__author__ = 'ufarooqi'
import os
import logging
import logging.config
import talent_property_manager

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# SQL ALCHEMY DB URL
GT_ENVIRONMENT = talent_property_manager.get_env()
if GT_ENVIRONMENT == 'dev':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@127.0.0.1/talent_local'
    BACKEND_URL = 'redis://localhost:6379'
    REDIS_URL = 'redis://localhost:6379'
    LOGGER = logging.getLogger("flask_service.dev")
elif GT_ENVIRONMENT == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    BACKEND_URL = 'redis://0.0.0.0:6379'
    REDIS_URL = 'redis://0.0.0.0:6379'
    LOGGER = logging.getLogger("flask_service.ci")
elif GT_ENVIRONMENT == 'qa':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    BACKEND_URL = 'dev-redis-vpc.znj3iz.0001.usw1.cache.amazonaws.com:6379'
    REDIS_URL = 'dev-redis-vpc.znj3iz.0001.usw1.cache.amazonaws.com:6379'
    LOGGER = logging.getLogger("flask_service.qa")
elif GT_ENVIRONMENT == 'prod':
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    BACKEND_URL = 'redis-prod.znj3iz.0001.usw1.cache.amazonaws.com:6379'
    REDIS_URL = 'redis-prod.znj3iz.0001.usw1.cache.amazonaws.com:6379'
    LOGGER = logging.getLogger("flask_service.prod")
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")


SECRET_KEY = talent_property_manager.get_secret_key()
OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 7200  # 2 hours expiry time for bearer token
