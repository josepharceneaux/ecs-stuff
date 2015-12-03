"""Initializer for SMS Campaign Service App"""

# Third Party
from flask import Flask
from healthcheck import HealthCheck

# Application Specific
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common import common_config
from sms_campaign_service.common.common_config import GT_ENVIRONMENT
from sms_campaign_service.common.error_handling import register_error_handlers
from sms_campaign_service.common.utils.models_utils import add_model_helpers, init_app

flask_app = Flask(__name__)
flask_app.config.from_object(common_config)

logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, "/healthcheck")


def init_sms_campaign_app():
    """
    Call this method at the start of app
    :return:
    """
    logger.info("sms_campaign_service is running in %s environment" % GT_ENVIRONMENT)
    return init_app(flask_app, logger)
