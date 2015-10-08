# -*- coding: utf-8 -*-
import os
from flask import Response
import logging
import time
import TalentPropertyManager

DO_BENCHMARKING = False  # Toggle whether to log time benchmarking info for the models

BENCHMARKING_START_DELTA = time.time()

IS_STAGING = False
IS_DEV_LOCAL = False

SOLR_HTTPAUTH_USER = 'codebox'
SOLR_HTTPAUTH_PASSWORD = 's*d=72ut;p;83Zd'

if TalentPropertyManager.get_env() == 'prod':
    HOST_NAME = "https://www.gettalent.com"
    OAUTH_SERVICE_HOST = "https://www.gettalent.com%s"
    # kaiser jobs search
    KAISER_SOLR_URL = 'http://ec2-54-176-0-133.us-west-1.compute.amazonaws.com:8983/solr/kaiser'
    DB_CONN = 'mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core'
    CACHE_SERVER_ENDPOINT = 'redis-prod.znj3iz.0001.usw1.cache.amazonaws.com:6379'
    IS_DEV = False
    logger = logging.getLogger("web2py.app.web_prod")
elif TalentPropertyManager.get_env() == 'qa':
    HOST_NAME = "https://webdev.gettalent.com"
    OAUTH_SERVICE_HOST = "https://secure-webdev.gettalent.com%s"
    # kaiser jobs search
    KAISER_SOLR_URL = 'http://webdev.gettalent.com:8983/solr/kaiser'
    DB_CONN = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    CACHE_SERVER_ENDPOINT = 'dev-redis-vpc.znj3iz.0001.usw1.cache.amazonaws.com:6379'
    IS_DEV = True
    logger = logging.getLogger("web2py.app.web_qa")
else:
    HOST_NAME = "http://127.0.0.1:8000"
    OAUTH_SERVICE_HOST = "http://127.0.0.1:8081%s"
    # kaiser jobs search
    KAISER_SOLR_URL = 'http://webdev.gettalent.com:8983/solr/kaiser'
    DB_CONN = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    CACHE_SERVER_ENDPOINT = '127.0.0.1:6379'
    IS_DEV = True
    IS_DEV_LOCAL = True
    logger = logging.getLogger("web2py.app.web_dev")

current.IS_DEV = IS_DEV
TCS_BUCKET_NAME = TalentPropertyManager.get_s3_bucket_name()
FILEPICKER_BUCKET_NAME = "gettalent-filepicker"

OAUTH_CLIENT_ID = "zGU2qD7pydK5pWY5WnnMHAoJRDWl3xIqLQWZMFtZ"
OAUTH_CLIENT_SECRET = "BHZxmEEA6CtA1vNmKBcZVdLlLEufb3O6SRbqNgvht74PoTFqb8"

# OAuth (Authentication) Service endpoints
OAUTH_SERVER = OAUTH_SERVICE_HOST % '/oauth2/token'
OAUTH_SERVER_AUTHORIZE = OAUTH_SERVICE_HOST % '/oauth2/authorize'
OAUTH_SERVER_REVOKE = OAUTH_SERVICE_HOST % '/oauth2/revoke'
OUTH_SERVICE_VERIFY_ROLES = OAUTH_SERVICE_HOST % '/roles/verify'
ADD_ROLES_TO_USER = OAUTH_SERVICE_HOST % '/users/%s/roles'

CLOUDSEARCH_REGION = TalentPropertyManager.get_cloudsearch_region()

#adding circleci specific configuration here.
# insert this condition in above if else statements, with respective solr and bucket names
if os.environ.get('CIRCLECI'):
    #DB_CONN = 'mysql://ubuntu@localhost/circle_test'  # CircleCI provides circle_test as default configured db.
    DB_CONN = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    logger = logging.getLogger("web2py.app.web_ci")

GOOGLE_ANALYTICS_TRACKING_ID = "UA-33209718-1"
HMAC_KEY = "s!web976892"

AWS_ACCESS_KEY_ID = 'AKIAI3422SZ6SL46EYBQ'
AWS_SECRET_ACCESS_KEY = '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'

NUANCE_OMNIPAGE_CLOUD_ACCOUNT_NAME = 'Eval4Osman_20120920'
NUANCE_OMNIPAGE_CLOUD_ACCOUNT_KEY = 'n8YCzECC4N5e/S3niBIfczsw3BrSBzNeTp+8LgxvMX8='

YAHOO_PLACEFINDER_APP_ID = "KNHq6P4q"
YAHOO_PLACEFINDER_CONSUMER_KEY = "dj0yJmk9OXpNcjdhUWpzV0pxJmQ9WVdrOVMwNUljVFpRTkhFbWNHbzlNVEF4TVRFeU16ZzJNZy0tJnM9Y29uc3VtZXJzZWNyZXQmeD1iMg--"
YAHOO_PLACEFINDER_CONSUMER_SECRET = "a74651047d03802c83b06d55168486c58eac7771"

HIPCHAT_TOKEN = 'ZmNg80eCeIN6sMCjIv03KNO2B4tqRcxTQNL44FBd'

SOCIALCV_API_KEY = "c96dfb6b9344d07cee29804152f798751ae8fdee"
STACKOVERFLOW_API_KEY = "hzOEoH16*Q7Y3QCWT9y)zA(("  # 10,000 requests is the limit

Response.headers['X-Talent-Id'] = TalentPropertyManager.get_instance_id()

if DO_BENCHMARKING:
    BENCHMARKING_END_DELTA = time.time()
    logger.info("TIME TO LOAD A_app_const: %s", BENCHMARKING_END_DELTA - BENCHMARKING_START_DELTA)
    BENCHMARKING_START_DELTA = BENCHMARKING_END_DELTA