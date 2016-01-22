""" Initializer for Push Campaign Service App.
"""

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


logger.info("push_campaign_service is running in %s environment" % flask_app.config[TalentConfigKeys.ENV_KEY])
app = init_talent_app(flask_app, logger)
CORS(app)
# Celery settings
celery_app = Celery(app, broker=app.config['BACKEND_URL'], backend=app.config['BACKEND_URL'],
                    include=['push_campaign_service.modules.push_campaign_base'])

