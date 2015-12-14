""" Initializer for SMS Campaign Service App and Celery App.

For Celery, Script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A sms_campaign_service.sms_campaign_app.app.celery_config.celery_app worker --concurrency=4 --loglevel=info

"""

# Third Party
from flask import Flask
from celery import Celery
from healthcheck import HealthCheck

# Application Specific
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common import common_config
from sms_campaign_service.common.common_config import BROKER_URL
from sms_campaign_service.common.common_config import GT_ENVIRONMENT
from sms_campaign_service.common.error_handling import register_error_handlers
from sms_campaign_service.common.utils.models_utils import add_model_helpers, init_app

flask_app = Flask(__name__)
flask_app.config.from_object(common_config)

logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, "/healthcheck")


def init_sms_campaign_app_and_celery_app():
    """
    Call this method at the start of app
    :return:
    """
    logger.info("sms_campaign_service is running in %s environment" % GT_ENVIRONMENT)
    initialized_app = init_app(flask_app, logger)

    # Celery settings
    celery_app = Celery(initialized_app, broker=BROKER_URL, backend=BROKER_URL,
                        include=['sms_campaign_service.sms_campaign_base'])
    return initialized_app, celery_app
