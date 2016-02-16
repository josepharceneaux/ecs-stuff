""" Initializer for SMS Campaign Service App and Celery App"""

# Third Party
from flask import Flask
from celery import Celery
from healthcheck import HealthCheck

# Common Utils
from sms_campaign_service.common.routes import HEALTH_CHECK
from sms_campaign_service.common.utils.models_utils import init_talent_app
from sms_campaign_service.common.talent_config_manager import TalentConfigKeys


app, logger = init_talent_app(Flask(__name__))
logger.info("sms_campaign_service is running in %s environment"
                % app.config[TalentConfigKeys.ENV_KEY])
# healthcheck URL
health = HealthCheck(app, HEALTH_CHECK)

try:
    # Celery settings
    celery_app = Celery(app, broker=app.config['REDIS_URL'],
                        backend=app.config['CELERY_RESULT_BACKEND_URL'],
                        include=['sms_campaign_service.modules.sms_campaign_base'])
except Exception as e:
    logger.exception("Couldn't start Celery app for sms_campaign_service in "
                     "%s environment." % (app.config[TalentConfigKeys.ENV_KEY]))
