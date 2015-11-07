"""Initializer for Social Network Service App"""
# Third Party
from datetime import timedelta
from flask import Flask
from flask.ext.celery import Celery

# Application Specific
from sms_campaign_service.common.models.db import db
from sms_campaign_service.model_helpers import add_model_helpers
from sms_campaign_service.common.error_handling import register_error_handlers

flask_app = Flask(__name__)
flask_app.config.from_object('sms_campaign_service.config')
logger = flask_app.config['LOGGER']

# Configuration for celery
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',
    # CELERYBEAT_SCHEDULE={
    #     '3-seconds': {
    #         'task': 'celery_task',
    #         'schedule': timedelta(seconds=3),
    #         'args': (16, 16)
    #     },
    # }
)

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
    register_error_handlers(flask_app, logger)
    return flask_app
