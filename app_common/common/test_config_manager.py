# -*- coding: utf-8 -*-
"""
This module contains utility method and class to load test configurations like test user_id, domain etc.

In a developer's local environment, the file given by the below LOCAL_CONFIG_PATH contains
the property keys and values.

﻿In prod and staging environments, the above config file does not exist.
Rather, the properties are obtained from ECS environment variables and a private S3 bucket.
"""
import os
import tempfile
import ConfigParser
from talent_config_manager import TalentConfigKeys, TalentEnvs

CONFIG_FILE_NAME = "common_test.cfg"
TEST_CONFIG_PATH = ".talent/%s" % CONFIG_FILE_NAME
STAGING_TEST_CONFIG_FILE_S3_BUCKET = "test-private-staging"
PROD_TEST_CONFIG_FILE_S3_BUCKET = "test-private"
JENKINS_TEST_CONFIG_FILE_S3_BUCKET = "test-private-jenkins"


# TODO ; Really great you created this file. Are we sure these above buckets are correct?

class TestConfigParser(ConfigParser.ConfigParser):

# TODO ; comment this class and the following method, also, rename 'k' to 'section'
    def to_dict(self):
        sections = dict(self._sections)
        for k in sections:
            sections[k] = dict(self._defaults, **sections[k])
            sections[k].pop('__name__', None)
        return sections


def load_test_config():
    """
    Load test configuration variables from test config file, conf file, or S3 bucket (if QA/prod)
    :return: config dict
    :rtype: dict
    """
    config_parse = TestConfigParser()
    env = os.getenv(TalentConfigKeys.ENV_KEY)
    if env == TalentEnvs.DEV:
        path = os.path.join(os.path.expanduser('~'), TEST_CONFIG_PATH)
        config_parse.read(path)
        test_config = config_parse.to_dict()

    # Load up config from private S3 bucket, if environment is qa or prod
    elif env in (TalentEnvs.QA, TalentEnvs.PROD, TalentEnvs.JENKINS):
        # Open S3 connection to default region & use AWS_ACCESS_KEY_ID and
        # AWS_SECRET_ACCESS_KEY env vars

        # TODO ; commment why this import here
        from boto.s3.connection import S3Connection
        s3_connection = S3Connection()
        if env == TalentEnvs.PROD:
            bucket_name = PROD_TEST_CONFIG_FILE_S3_BUCKET
        elif env == TalentEnvs.QA:
            bucket_name = STAGING_TEST_CONFIG_FILE_S3_BUCKET
        else:
            bucket_name = JENKINS_TEST_CONFIG_FILE_S3_BUCKET
        bucket_obj = s3_connection.get_bucket(bucket_name)
        # Download into temporary file & load it as a Python module into the app_config
        tmp_test_config_file = tempfile.NamedTemporaryFile()
        bucket_obj.get_key(key_name=CONFIG_FILE_NAME).get_contents_to_file(tmp_test_config_file)
        tmp_test_config_file.file.seek(0)
        config_parse.read(tmp_test_config_file.name)
        test_config = config_parse.to_dict()
        tmp_test_config_file.close()
    else:
        raise Exception("Environment is not properly set, given value for GT_ENVIRONMENT: %s" % env)

    return test_config

