""" Initializer for SMS Campaign Service App and Celery App"""

# Third Party
from flask import Flask
from celery import Celery
from healthcheck import HealthCheck

# Common Utils
from sms_campaign_service.common.utils.models_utils import init_talent_app
from sms_campaign_service.common.utils.talent_ec2 import get_ec2_instance_id
from sms_campaign_service.common.talent_config_manager import (load_gettalent_config,
                                                               TalentConfigKeys)

flask_app = Flask(__name__)
load_gettalent_config(flask_app.config)

# logger setup
logger = flask_app.config[TalentConfigKeys.LOGGER]
logger.info("Starting app %s in EC2 instance %s", flask_app.import_name, get_ec2_instance_id())
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
    celery_app = Celery(initialized_app, broker=initialized_app.config['REDIS_URL'],
                        backend=initialized_app.config['CELERY_RESULT_BACKEND_URL'],
                        include=['sms_campaign_service.modules.sms_campaign_base'])
    return initialized_app, celery_app

try:
    # Initializing App. This line should come before any imports from models
    app, celery_app = init_sms_campaign_app_and_celery_app()
except Exception as e:
    logger.exception("Couldn't start sms_campaign_service in %s environment."
                     % (flask_app.config[TalentConfigKeys.ENV_KEY]))
