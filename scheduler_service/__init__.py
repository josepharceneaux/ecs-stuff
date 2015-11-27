import os
from flask import Flask
from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models.db import db
from scheduler_service.model_helpers import add_model_helpers
from tasks import app
import logging as logger

__author__ = 'saad'


flask_app = Flask(__name__)
flask_app.config.from_object('scheduler_service.config')
logger = flask_app.config['LOGGER']


def init_app():
    """
    Call this method at the start of app or manager for Events/RSVPs
    :return:
    """
    add_model_helpers(db.Model)
    db.init_app(flask_app)
    db.app = flask_app
    db.create_all()
    register_error_handlers(flask_app, logger)
    logger.info("Starting scheduling_service in %s environment",
                os.environ['GT_ENVIRONMENT'])

    return flask_app
