# -*- coding: utf-8 -*-
"""Class to manage property keys and values specific to the application environment (e.g. prod, staging, local).

In a developer's local environment, the file given by the below LOCAL_CONFIG_PATH contains the property keys and values.

﻿In prod and staging environments, the above config file does not exist.
Rather, the properties are obtained from ECS Environment Variables.
"""

import os
import logging
import logging.config
from flask.config import Config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

LOCAL_CONFIG_PATH = ".talent/web.cfg"


class ConfigKeys(object):

    CS_REGION_KEY = "CLOUD_SEARCH_REGION"
    CS_DOMAIN_KEY = "CLOUD_SEARCH_DOMAIN"
    EMAIL_KEY = "EMAIL"
    ENV_KEY = "GT_ENVIRONMENT"
    ACCOUNT_ID_KEY = "ACCOUNT_ID"
    S3_BUCKET_KEY = "S3_BUCKET_NAME"
    S3_REGION_KEY = "S3_BUCKET_REGION"
    S3_FILE_PICKER_BUCKET_KEY = "S3_FILEPICKER_BUCKET_NAME"
    INSTANCE_NAME = 'INSTANCE_NAME'
    AWS_KEY = "AWS_ACCESS_KEY_ID"
    AWS_SECRET = "AWS_SECRET_ACCESS_KEY"
    SECRET_KEY = "SECRET_KEY"
    LOGGER = "LOGGER"


class TalentConfig(Config):

    app_config = None

    def __init__(self, app_config):

        app_config.root_path = os.path.expanduser('~')

        # LOCAL_CONFIG_PATH will not exist for Production and QA that's why we provided silent=True to avoid exception
        app_config.from_pyfile(LOCAL_CONFIG_PATH, silent=True)

        for key, value in ConfigKeys.__dict__.iteritems():
            if not key.startswith('__'):

                # If a configuration variable is set in environment variables then it should be given preference
                app_config[value] = os.getenv(value) or app_config.get(value, '')

        self.app_config = app_config
        self.__set_environment_specific_configurations()

    def __set_environment_specific_configurations(self):

        environment = self.app_config.get(ConfigKeys.ENV_KEY)

        if environment == 'dev':
            self.app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_web:s!loc976892@127.0.0.1/talent_local'
            self.app_config['BACKEND_URL'] = self.app_config['REDIS_URL'] = 'redis://localhost:6379'
            self.app_config['LOGGER'] = logging.getLogger("flask_service.dev")
            self.app_config['DEBUG'] = True
        elif environment == 'circle':
            self.app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west' \
                                                         '-1.rds.amazonaws.com/talent_ci'
            self.app_config['BACKEND_URL'] = self.app_config['REDIS_URL'] = 'redis://localhost:6379'
            self.app_config['LOGGER'] = logging.getLogger("flask_service.ci")
            self.app_config['DEBUG'] = True
        elif environment == 'qa':
            self.app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_web:s!web976892@devdb.gettalent.' \
                                                         'com/talent_staging'
            self.app_config['BACKEND_URL'] = self.app_config['REDIS_URL'] = 'dev-redis-vpc.znj3iz.0001.usw1.cache.' \
                                                                            'amazonaws.com:6379'
            self.app_config['LOGGER'] = logging.getLogger("flask_service.qa")
        elif environment == 'prod':
            self.app_config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_STRING')
            self.app_config['BACKEND_URL'] = self.app_config['REDIS_URL'] = 'redis-prod.znj3iz.0001.' \
                                                                            'usw1.cache.amazonaws.com:6379'
            self.app_config['LOGGER'] = logging.getLogger("flask_service.prod")
        else:
            raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

        self.app_config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'] = 7200  # 2 hours expiry time for bearer token





