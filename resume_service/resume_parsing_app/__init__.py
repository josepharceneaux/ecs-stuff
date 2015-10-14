"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'

from views import api
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import config

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)

app.register_blueprint(api.mod)

logger = app.config['LOGGER']

from common.error_handling import register_error_handlers

register_error_handlers(app, logger)

logger.info("Starting resume_service in %s environment", app.config['GT_ENVIRONMENT'])
