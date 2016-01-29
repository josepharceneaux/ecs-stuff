""" Initializer for Push Campaign Service App.
"""
__author__ = 'Zohaib Ijaz <mzohaib.qc@gnail.com>'
# Third Party
from flask import Flask
from celery import Celery
from flask.ext.cors import CORS
from healthcheck import HealthCheck


# Application Specific
from push_campaign_service.common.utils.models_utils import init_talent_app
from push_campaign_service.common.talent_config_manager import (load_gettalent_config,
                                                                TalentConfigKeys)

flask_app = Flask(__name__)
load_gettalent_config(flask_app.config)

logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, "/healthcheck")


def init_push_campaign_app_and_celery_app():
    """
    Call this method at the start of app
    :return:
    """
    logger.info("push_campaign_service is running in %s environment"
                % flask_app.config[TalentConfigKeys.ENV_KEY])
    initialized_app = init_talent_app(flask_app, logger)
    # Celery settings
    celery_app = Celery(initialized_app, broker=initialized_app.config['REDIS_URL'],
                        backend=initialized_app.config['CELERY_RESULT_BACKEND_URL'],
                        include=['push_campaign_service.modules.push_campaign_base'])
    return initialized_app, celery_app

try:
    # Initializing App. This line should come before any imports from models
    app, celery_app = init_push_campaign_app_and_celery_app()
except Exception as e:
    logger.exception("Couldn't start push_campaign_service in %s environment."
                     % (flask_app.config[TalentConfigKeys.ENV_KEY]))

