"""Initializer for Social Network Service App"""
from types import MethodType
from social_network_service.model_helpers import add_model_helpers

__author__ = 'zohaib'

from flask import Flask
from common.models.db import db

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
    return flask_app
