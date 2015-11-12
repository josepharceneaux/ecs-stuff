"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'

from views import api
from flask import Flask
from common.models.db import db

import config

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
db.app = app

app.register_blueprint(api.mod, url_prefix='/v1')

logger = app.config['LOGGER']

from common.error_handling import register_error_handlers

register_error_handlers(app, logger)

logger.info("Starting resume_service in %s environment", app.config['GT_ENVIRONMENT'])
