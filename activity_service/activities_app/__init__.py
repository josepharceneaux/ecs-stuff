"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask
from activity_service.common.models.db import db
from views import api
from activity_service.common.error_handling import register_error_handlers


app = Flask(__name__)
app.config.from_object('activity_service.config')
app.register_blueprint(api.mod)

logger = app.config['LOGGER']

db.init_app(app)
db.app = app

register_error_handlers(app, logger)

logger.info("Starting activity_service in %s environment", app.config['GT_ENVIRONMENT'])
