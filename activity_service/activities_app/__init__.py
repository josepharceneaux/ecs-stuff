"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask
from common.models.db import db
from views import api
from common.error_handling import register_error_handlers
from healthcheck import HealthCheck

app = Flask(__name__)
app.config.from_object('activity_service.config')
app.register_blueprint(api.mod)

logger = app.config['LOGGER']

db.init_app(app)
db.app = app

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

register_error_handlers(app, logger)

logger.info("Starting activity_service in %s environment", app.config['GT_ENVIRONMENT'])
