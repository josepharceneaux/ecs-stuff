import os
from flask import Flask
from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models.db import db
from scheduler_service.common.utils.models_utils import add_model_helpers

__author__ = 'saad'


flask_app = Flask(__name__)
flask_app.config.from_object('scheduler_service.common.common_config')
logger = flask_app.config['LOGGER']


def init_app():
    """
    Call this method at the start of app
    :return:
    """
    add_model_helpers(db.Model, logger=logger)
    db.init_app(flask_app)
    db.app = flask_app
    db.create_all()
    register_error_handlers(flask_app, logger)

    return flask_app
