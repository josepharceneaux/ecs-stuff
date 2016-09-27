# -*- coding: utf-8 -*-
"""Class to manage property keys and values specific to the application environment (e.g. prod, staging, local).

In a developer's local environment, the file given by the below LOCAL_CONFIG_PATH contains the property keys and values.

﻿In prod and staging environments, the above config file does not exist.
Rather, the properties are obtained from ECS environment variables and a private S3 bucket.
"""

import imp
import logging
import logging.config
import os
import tempfile

# Load logging configuration file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(APP_ROOT, 'logging.conf')
logging.config.fileConfig(LOGGING_CONF)

# Kindly refer to following url for sample web.cfg
# https://github.com/gettalent/talent-flask-services/wiki/Local-environment-setup#local-configurations
CONFIG_FILE_NAME = "web.cfg"
LOCAL_CONFIG_PATH = ".talent/%s" % CONFIG_FILE_NAME
STAGING_CONFIG_FILE_S3_BUCKET = "gettalent-private-staging"
PROD_CONFIG_FILE_S3_BUCKET = "gettalent-private"
JENKINS_CONFIG_FILE_S3_BUCKET = "gettalent-private-jenkins"


class TalentConfigKeys(object):
    AWS_KEY = "AWS_ACCESS_KEY_ID"
    AWS_SECRET = "AWS_SECRET_ACCESS_KEY"
    BG_URL="BG_URL"
    CELERY_RESULT_BACKEND_URL = 'CELERY_RESULT_BACKEND_URL'
    CONSUMER_SECRET="CONSUMER_SECRET"
    CS_DOMAIN_KEY = "CLOUD_SEARCH_DOMAIN"
    CS_REGION_KEY = "CLOUD_SEARCH_REGION"
    DEFAULT_MAIL_SENDER = "DEFAULT_MAIL_SENDER"
    EMAIL_KEY = "EMAIL"
    ENV_KEY = "GT_ENVIRONMENT"
    EVENTBRITE_ACCESS_TOKEN = "EVENTBRITE_ACCESS_TOKEN"
    GOOGLE_API_KEY="GOOGLE_API_KEY"
    GOOGLE_CLOUD_VISION_URL="GOOGLE_CLOUD_VISION_URL"
    GOOGLE_URL_SHORTENER_API_KEY = "GOOGLE_URL_SHORTENER_API_KEY"
    GT_GMAIL_ID = "GT_GMAIL_ID"
    GT_GMAIL_PASSWORD = "GT_GMAIL_PASSWORD"
    IMAAS_KEY = "IMAAS_KEY"
    IMAAS_URL = "IMAAS_URL"
    LOGGER = "LOGGER"
    MEETUP_ACCESS_TOKEN = "MEETUP_ACCESS_TOKEN"
    MEETUP_REFRESH_TOKEN = "MEETUP_REFRESH_TOKEN"
    ONE_SIGNAL_APP_ID = "ONE_SIGNAL_APP_ID"
    ONE_SIGNAL_REST_API_KEY = "ONE_SIGNAL_REST_API_KEY"
    REDIS_URL_KEY = "REDIS_URL"
    S3_BUCKET_KEY = "S3_BUCKET_NAME"
    S3_FILE_PICKER_BUCKET_KEY = "S3_FILEPICKER_BUCKET_NAME"
    S3_REGION_KEY = "S3_BUCKET_REGION"
    SECRET_KEY = "SECRET_KEY"
    TOKEN_SECRET = "TOKEN_SECRET"
    TWILIO_ACCOUNT_SID = "TWILIO_ACCOUNT_SID"
    TWILIO_AUTH_TOKEN = "TWILIO_AUTH_TOKEN"
    SLACK_BOT_TOKEN = "SLACK_BOT_TOKEN"
    MAILGUN_API_KEY = "MAILGUN_API_KEY"
    FACEBOOK_ACCESS_TOKEN = "FACEBOOK_ACCESS_TOKEN"
    SLACK_APP_CLIENT_ID = "SLACK_APP_CLIENT_ID"
    SLACK_APP_CLIENT_SECRET = "SLACK_APP_CLIENT_SECRET"
    JENKINS_HOST_IP = "JENKINS_HOST_IP"
    ENCRYPTION_KEY = 'ENCRYPTION_KEY'


class TalentEnvs(object):
    """
    Here are the values of different environments used for getTalent app.
    """
    DEV = 'dev'
    JENKINS = 'jenkins'
    QA = 'qa'
    PROD = 'prod'


def load_gettalent_config(app_config):
    """
    Load configuration variables from env vars, conf file, or S3 bucket (if QA/prod)
    :param flask.config.Config app_config: Flask configuration object
    :return: None
    """
    app_config.root_path = os.path.expanduser('~')

    # Load up config from file on local filesystem (for local dev & Jenkins only).
    app_config.from_pyfile(LOCAL_CONFIG_PATH, silent=True)  # silent=True avoids errors in CI/QA/prod envs

    # Make sure that the environment and AWS credentials are defined
    for config_field_key in (TalentConfigKeys.ENV_KEY, TalentConfigKeys.AWS_KEY, TalentConfigKeys.AWS_SECRET):
        app_config[config_field_key] = app_config.get(config_field_key) or os.environ.get(config_field_key)
        if not app_config.get(config_field_key):
            raise Exception("Loading getTalent config: Missing required environment variable: %s" % config_field_key)
    app_config[TalentConfigKeys.ENV_KEY] = app_config[TalentConfigKeys.ENV_KEY].strip().lower()
    app_config[TalentConfigKeys.LOGGER] = logging.getLogger("flask_service.%s" % app_config[TalentConfigKeys.ENV_KEY])

    # Load up config from private S3 bucket, if environment is qa or prod
    if app_config[TalentConfigKeys.ENV_KEY] in (TalentEnvs.QA, TalentEnvs.PROD, TalentEnvs.JENKINS):
        # Open S3 connection to default region & use AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars
        from boto.s3.connection import S3Connection
        s3_connection = S3Connection()
        if app_config[TalentConfigKeys.ENV_KEY] == TalentEnvs.PROD:
            bucket_name = PROD_CONFIG_FILE_S3_BUCKET
        elif app_config[TalentConfigKeys.ENV_KEY] == TalentEnvs.QA:
            bucket_name = STAGING_CONFIG_FILE_S3_BUCKET
        else:
            bucket_name = JENKINS_CONFIG_FILE_S3_BUCKET

        bucket_obj = s3_connection.get_bucket(bucket_name)
        app_config[TalentConfigKeys.LOGGER].info("Loading getTalent config from private S3 bucket %s", bucket_name)

        # Download into temporary file & load it as a Python module into the app_config
        tmp_config_file = tempfile.NamedTemporaryFile()
        bucket_obj.get_key(key_name=CONFIG_FILE_NAME).get_contents_to_file(tmp_config_file)
        tmp_config_file.file.seek(0)  # For some reason, get_contents_to_file doesn't reset file handle
        data = imp.load_source('data', '', tmp_config_file.file)
        app_config.from_object(data)
        tmp_config_file.close()
    # Load up hardcoded app config values
    _set_environment_specific_configurations(app_config[TalentConfigKeys.ENV_KEY], app_config)
    # Verify that all the TalentConfigKeys have been defined in the app config (one way or another)
    missing_config_value = missing_config_key_definition(app_config)
    if missing_config_value:
        raise Exception("Required app config key not defined: %s" % missing_config_value)
    app_config['LOGGER'].info("App configuration successfully loaded with %s keys: %s", len(app_config), app_config.keys())
    app_config['LOGGER'].debug("App configuration: %s", app_config)


def _set_environment_specific_configurations(environment, app_config):
    app_config['DEBUG'] = False

    if environment == TalentEnvs.DEV:
        app_config['CELERY_RESULT_BACKEND_URL'] = app_config['REDIS_URL'] = 'redis://localhost:6379'
        app_config['REDIS2_DB'] = 1
        app_config['DEBUG'] = True
        app_config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'] = 7200
        app_config['JWT_OAUTH_EXPIRATION'] = 3600 * 24 * 7  # One week expiry time for bearer token
        app_config['SQLALCHEMY_DATABASE_URI'] = 'mysql://talent_web:s!loc976892@127.0.0.1/talent_local'


def missing_config_key_definition(app_config):
    """
    If a TalentConfigKey is not defined, return it.

    :rtype: str | None
    """

    # Filter out all private methods/fields of the object class
    all_config_keys = filter(lambda possible_config_key: not possible_config_key.startswith("__"),
                             dir(TalentConfigKeys))

    for config_key in all_config_keys:
        app_config_field_name = getattr(TalentConfigKeys, config_key)
        if not app_config.get(app_config_field_name):
            return app_config_field_name
