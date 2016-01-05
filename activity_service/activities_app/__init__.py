"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask
from healthcheck import HealthCheck
from activity_service.common.models.db import db
from activity_service.common.error_handling import register_error_handlers
from activity_service.common.talent_config_manager import TalentConfig, ConfigKeys

app = Flask(__name__)
app.config = TalentConfig(app.config).app_config


from views import api
app.register_blueprint(api.mod)

logger = app.config[ConfigKeys.LOGGER]

db.init_app(app)
db.app = app

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

register_error_handlers(app, logger)

logger.info("Starting activity_service in %s environment", app.config[ConfigKeys.ENV_KEY])
