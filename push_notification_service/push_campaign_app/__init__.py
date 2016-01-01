""" Initializer for Push Campaign Service App.
"""

# Third Party
from flask import Flask
from healthcheck import HealthCheck

# Application Specific
from push_notification_service.common import common_config
from push_notification_service.common.common_config import GT_ENVIRONMENT
from push_notification_service.common.utils.models_utils import init_talent_app

flask_app = Flask(__name__)
flask_app.config.from_object(common_config)

logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, "/healthcheck")


def init_push_notification_app():
    """
    Call this method at the start of app
    :return:
    """
    logger.info("push_notification_service is running in %s environment" % GT_ENVIRONMENT)
    app = init_talent_app(flask_app, logger)
    return app
