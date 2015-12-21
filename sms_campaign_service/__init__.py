""" Initializer for SMS Campaign Service App and Celery App"""

# Third Party
from flask import Flask
from celery import Celery
from healthcheck import HealthCheck

# Database Models
from sms_campaign_service.common.models.db import db

# Common Utils
from sms_campaign_service.common import common_config
from sms_campaign_service.common.common_config import REDIS_SERVER_URL
from sms_campaign_service.common.common_config import GT_ENVIRONMENT
from sms_campaign_service.common.error_handling import register_error_handlers
from sms_campaign_service.common.utils.models_utils import add_model_helpers, init_talent_app

flask_app = Flask(__name__, static_url_path='')
flask_app.config.from_object(common_config)

# logger setup
logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, "/healthcheck")


def init_sms_campaign_app_and_celery_app():
    """
    Call this method at the start of app
    :return:
    """
    logger.info("sms_campaign_service is running in %s environment" % GT_ENVIRONMENT)
    initialized_app = init_talent_app(flask_app, logger)

    # Celery settings
    celery_app = Celery(initialized_app, broker=REDIS_SERVER_URL, backend=REDIS_SERVER_URL,
                        include=['sms_campaign_service.sms_campaign_base'])
    return initialized_app, celery_app
