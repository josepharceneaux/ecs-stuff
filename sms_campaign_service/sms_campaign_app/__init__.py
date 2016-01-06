""" Initializer for SMS Campaign Service App and Celery App"""

# Third Party
from flask import Flask
from celery import Celery
from healthcheck import HealthCheck

# Common Utils
from sms_campaign_service.common.utils.models_utils import init_talent_app
from sms_campaign_service.common.talent_config_manager import (load_gettalent_config,
                                                               TalentConfigKeys)


flask_app = Flask(__name__)
load_gettalent_config(flask_app.config)

# logger setup
logger = flask_app.config[TalentConfigKeys.LOGGER]

health = HealthCheck(flask_app, "/healthcheck")


def init_sms_campaign_app_and_celery_app():
    """
    Call this method at the start of app
    :return:
    """
    logger.info("sms_campaign_service is running in %s environment"
                % flask_app.config[TalentConfigKeys.ENV_KEY])
    initialized_app = init_talent_app(flask_app, logger)
    # Celery settings
    celery_app = Celery(initialized_app, broker=initialized_app.config['BACKEND_URL'],
                        backend=flask_app.config['BACKEND_URL'],
                        include=['sms_campaign_service.sms_campaign_base'])
    # load_gettalent_config(celery_app.conf)
    return initialized_app, celery_app

# Initializing App. This line should come before any imports from models
app, celery_app = init_sms_campaign_app_and_celery_app()
