"""Initializer for Social Network Service App"""
# Third Party
from flask import Flask
from flask.ext.celery import Celery

# Application Specific
from common.models.db import db
from social_network_service.model_helpers import add_model_helpers

flask_app = Flask(__name__)
flask_app.config.from_object('sms_campaign_service.config')
logger = flask_app.config['LOGGER']
# flask_app.config['CELERY_BROKER_URL'] = 'redis://localhost'
# flask_app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost'
# celery = Celery(flask_app)


def init_app():
    """
    Call this method at the start of app or manager for Events/RSVPs
    :return:
    """
    add_model_helpers(db.Model)
    db.init_app(flask_app)
    db.app = flask_app
    return flask_app
