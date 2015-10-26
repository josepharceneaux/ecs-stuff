"""Initializer for Search Candidates App"""

from flask import Flask
from common.models.db import db
from common.error_handling import register_error_handlers
from views import api
from candidate_service import config

__author__ = 'naveen'

app = Flask(__name__)

app.config.from_object(config)

app.register_blueprint(api.mod)

logger = app.config['LOGGER']

register_error_handlers(app, logger)

db.init_app(app)

db.app = app

logger.info("Starting search_service in %s environment", app.config['GT_ENVIRONMENT'])
