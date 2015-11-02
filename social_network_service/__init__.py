"""Initializer for Social Network Service App"""
__author__ = 'zohaib'

from flask import Flask

from social_network_service.common.models.db import db
from social_network_service.common.error_handling import register_error_handlers
from social_network_service.model_helpers import add_model_helpers

flask_app = Flask(__name__)
flask_app.config.from_object('social_network_service.config')
logger = flask_app.config['LOGGER']


def init_app():
    """
    Call this method at the start of app or manager for Events/RSVPs
    :return:
    """
    add_model_helpers(db.Model)
    db.init_app(flask_app)
    db.app = flask_app
    register_error_handlers(flask_app, logger)
    logger.info("Starting social network service in %s environment",
                flask_app.config['GT_ENVIRONMENT'])
    return flask_app

