"""Initialize Email campaign service app, register error handlers and register blueprint"""

from flask import Flask
from celery import Celery
from healthcheck import HealthCheck
from email_campaign_service.common.models.db import db
from email_campaign_service.common.routes import HEALTH_CHECK
from email_campaign_service.common.utils.models_utils import init_talent_app
from email_campaign_service.common.talent_config_manager import TalentConfigKeys

app, logger = init_talent_app(Flask(__name__))
try:
    # Initialize Celery app
    celery_app = Celery(app, broker=app.config['REDIS_URL'],
                        backend=app.config['CELERY_RESULT_BACKEND_URL'],
                        include=['email_campaign_service.modules.email_marketing'])
    # wrap the flask app and give a healthcheck url
    health = HealthCheck(app, HEALTH_CHECK)

    from apis.email_campaigns import email_campaign_blueprint
    app.register_blueprint(email_campaign_blueprint)

    logger.info('Starting email_campaign_service in %s environment'
                % app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start email_campaign_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
