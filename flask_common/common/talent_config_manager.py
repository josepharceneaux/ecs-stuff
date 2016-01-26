# -*- coding: utf-8 -*-
"""Class to manage property keys and values specific to the application environment (e.g. prod, staging, local).

In a developer's local environment, the file given by the below LOCAL_CONFIG_PATH contains the property keys and values.

﻿In prod and staging environments, the above config file does not exist.
Rather, the properties are obtained from ECS Environment Variables.
"""

import os
import logging
import logging.config

# load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)


# Kindly refer to following url for sample web.cfg
# https://github.com/gettalent/talent-flask-services/wiki/Local-environment-setup#local-configurations
LOCAL_CONFIG_PATH = ".talent/web.cfg"


class TalentConfigKeys(object):
    CS_REGION_KEY = "CLOUD_SEARCH_REGION"
    CS_DOMAIN_KEY = "CLOUD_SEARCH_DOMAIN"
    EMAIL_KEY = "EMAIL"
    ENV_KEY = "GT_ENVIRONMENT"
    S3_BUCKET_KEY = "S3_BUCKET_NAME"
    S3_REGION_KEY = "S3_BUCKET_REGION"
    S3_FILE_PICKER_BUCKET_KEY = "S3_FILEPICKER_BUCKET_NAME"
    AWS_KEY = "AWS_ACCESS_KEY_ID"
    AWS_SECRET = "AWS_SECRET_ACCESS_KEY"
    SECRET_KEY = "SECRET_KEY"
    LOGGER = "LOGGER"
    MEETUP_ACCESS_TOKEN = 'MEETUP_ACCESS_TOKEN'
    MEETUP_REFRESH_TOKEN = 'MEETUP_REFRESH_TOKEN'
    EVENTBRITE_ACCESS_TOKEN = 'EVENTBRITE_ACCESS_TOKEN'


def load_gettalent_config(app_config):
    """
    Load configuration variables from conf file or environment varaibles
    :param flask.config.Config app_config: Flask configuration object
    :return: None
    """

    app_config.root_path = os.path.expanduser('~')

    # Load up config from file on local filesystem (for local dev only).
    app_config.from_pyfile(LOCAL_CONFIG_PATH, silent=True)  # silent=True avoids errors in CI/QA/prod envs

    for key, value in TalentConfigKeys.__dict__.iteritems():
        if not key.startswith('__'):

            # If a configuration variable is set in environment variables then it should be given preference
            app_config[value] = os.getenv(value) or app_config.get(value, '')
            if not app_config[value] and value != 'LOGGER':
                raise Exception('Configuration variable: "%s" is missing' % value)

    _set_environment_specific_configurations(app_config)


def _set_environment_specific_configurations(app_config):

    environment = app_config.get(TalentConfigKeys.ENV_KEY)
    app_config['DEBUG'] = False

    if environment == 'dev':
        app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_web:s!loc976892@127.0.0.1/talent_local'
        app_config['CELERY_RESULT_BACKEND_URL'] = app_config['REDIS_URL'] = 'redis://localhost:6379'
        app_config['LOGGER'] = logging.getLogger("flask_service.dev")
        app_config['DEBUG'] = True
    elif environment == 'jenkins':
        app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent-jenkins:s!jenkins976892@jenkins.gettalent.com/talent_jenkins'
        app_config['CELERY_RESULT_BACKEND_URL'] = app_config['REDIS_URL'] = 'redis://:s!jenkinsRedis974812@jenkins.gettalent.com:6379'
        app_config['LOGGER'] = logging.getLogger("flask_service.jenkins")
    elif environment == 'qa':
        app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_web:s!web976892@devdb.gettalent.' \
                                                     'com/talent_staging'
        app_config['CELERY_RESULT_BACKEND_URL'] = app_config['REDIS_URL'] = 'dev-redis-vpc.znj3iz.0001.usw1.cache.' \
                                                                        'amazonaws.com:6379'
        app_config['LOGGER'] = logging.getLogger("flask_service.qa")
    elif environment == 'prod':
        app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core'
        app_config['CELERY_RESULT_BACKEND_URL'] = app_config['REDIS_URL'] = 'redis-prod.znj3iz.0001.' \
                                                                        'usw1.cache.amazonaws.com:6379'
        app_config['LOGGER'] = logging.getLogger("flask_service.prod")
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

    app_config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'] = 7200  # 2 hours expiry time for bearer token
