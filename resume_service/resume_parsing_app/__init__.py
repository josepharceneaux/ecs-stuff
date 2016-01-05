"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'
# Third party
from flask import Flask
# Module specific
from resume_service.common.models.db import db
from resume_service.common.talent_config_manager import TalentConfig, ConfigKeys
from healthcheck import HealthCheck
import config

app = Flask(__name__)
app.config = TalentConfig(app.config).app_config
app.config.from_object(config)

db.init_app(app)
db.app = app

from views import api
app.register_blueprint(api.mod, url_prefix='/v1')

logger = app.config[ConfigKeys.LOGGER]

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from resume_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

logger.info("Starting resume_service in %s environment", app.config[ConfigKeys.ENV_KEY])
