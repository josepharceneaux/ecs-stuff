""" Initializer for Social Network Service App.
"""
__author__ = 'zohaib'

# Third Party
from flask import Flask
from flask.ext.cors import CORS
from healthcheck import HealthCheck


# Application Specific
from social_network_service.common.routes import HEALTH_CHECK
from social_network_service.common.utils.models_utils import init_app
from social_network_service.common.talent_config_manager import (load_gettalent_config,
                                                                 TalentConfigKeys)

flask_app = Flask(__name__)
load_gettalent_config(flask_app.config)

logger = flask_app.config['LOGGER']

health = HealthCheck(flask_app, HEALTH_CHECK)


logger.info("social_network_service is running in %s environment"
            % flask_app.config[TalentConfigKeys.ENV_KEY])
app = init_app(flask_app, logger)
CORS(app)





