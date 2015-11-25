from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models import db
from scheduler_service.model_helpers import add_model_helpers
from tasks import app
import logging as logger

__author__ = 'saad'

logger.basicConfig()


def init_app():
    """
    Call this method at the start of app or manager for Events/RSVPs
    :return:
    """
    app.config.from_object('config')
    register_error_handlers(app, logger=None)
    return app
