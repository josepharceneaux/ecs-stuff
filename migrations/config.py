import os
import logging

# Flask SQLAlchemy database URLs
if os.environ.get('GT_ENVIRONMENT') == 'dev':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'circle':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    DEBUG = True
elif os.environ.get('GT_ENVIRONMENT') == 'qa':
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    DEBUG = False
elif os.environ.get('GT_ENVIRONMENT') == 'prod':
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_STRING')
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")