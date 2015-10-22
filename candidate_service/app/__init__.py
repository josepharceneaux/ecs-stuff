import config
from flask import Flask
from candidate_service.common.models.db import db
from common.error_handling import register_error_handlers

# Initiate flask app and configure the application
app = Flask(__name__)
app.config.from_object(obj=config)

# Initialize application with database setup
db.init_app(app=app)
db.app = app

# Configure logger
logger = app.config['LOGGER']

register_error_handlers(app=app, logger=logger)

# logger.info("Starting candidate_service in %s environment", app.config['GT_ENVIRONMENT'])