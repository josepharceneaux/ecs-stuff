""" Initializer for Push Campaign Service App.
"""

# Third Party
from flask import Flask
from celery import Celery
from healthcheck import HealthCheck


# Application Specific
from push_campaign_service.common.utils.models_utils import init_talent_app
from push_campaign_service.common.talent_config_manager import (load_gettalent_config,
                                                                TalentConfigKeys)

flask_app = Flask(__name__)
load_gettalent_config(flask_app.config)

logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, "/healthcheck")


# def init_push_notification_app():
#     """
#     Call this method at the start of app and initialized celery app
#     :return:
#     """
#     logger.info("push_campaign_service is running in %s environment" % GT_ENVIRONMENT)
#     app = init_talent_app(flask_app, logger)
#     # Celery settings
#     celery_app = Celery(app, broker=REDIS_SERVER_URL, backend=REDIS_SERVER_URL,
#                         include=['push_campaign_service.modules.push_campaign_base'])
#     app.celery = celery_app
#     return app

logger.info("push_campaign_service is running in %s environment" % flask_app.config[TalentConfigKeys.ENV_KEY])
app = init_talent_app(flask_app, logger)
# Celery settings
celery_app = Celery(app, broker=app.config['BACKEND_URL'], backend=app.config['BACKEND_URL'],
                    include=['push_campaign_service.modules.push_campaign_base'])

