"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'

from flask import Flask
from views import api
from resume_service.common.models.db import db
from resume_service.common.models.candidate import *
from resume_service.common.models.user import *

app = Flask(__name__)
app.config.from_object('resume_service.config')
app.register_blueprint(api.mod)
logger = app.config['LOGGER']

db.init_app(app)
db.app = app

from common.error_handling import register_error_handlers

register_error_handlers(app, logger)

logger.info("Starting resume_service in %s environment", app.config['GT_ENVIRONMENT'])
