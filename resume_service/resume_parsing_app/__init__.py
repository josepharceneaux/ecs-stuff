"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'

from views import api
from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
from resume_service.common.models.db import db
from healthcheck import HealthCheck
import config

app = Flask(__name__)
app.config.from_object(config)
# db = SQLAlchemy(app)
db.init_app(app)
db.app = app

app.register_blueprint(api.mod)

logger = app.config['LOGGER']

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from resume_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

logger.info("Starting resume_service in %s environment", app.config['GT_ENVIRONMENT'])
