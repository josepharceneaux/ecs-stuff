import os
import logging

# Flask SQLAlchemy database URLs
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    LOGGER = logging.getLogger("auth_service.web_dev")
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
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