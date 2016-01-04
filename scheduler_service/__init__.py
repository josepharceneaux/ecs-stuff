from celery import Celery
from flask import Flask
from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models.db import db
from scheduler_service.common.redis_cache import redis_store
from scheduler_service.common.utils.models_utils import add_model_helpers
from scheduler_service.common.common_config import BACKEND_URL, REDIS_URL


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
    # Initialize Redis Cache
    redis_store.init_app(flask_app)
    register_error_handlers(flask_app, logger)
    logger.info("Starting scheduler service in %s environment",
                flask_app.config['GT_ENVIRONMENT'])

    # Celery settings
    celery_app = Celery(flask_app, broker=REDIS_URL, backend=BACKEND_URL,
                        include=['scheduler_service.tasks'])
    return flask_app, celery_app
