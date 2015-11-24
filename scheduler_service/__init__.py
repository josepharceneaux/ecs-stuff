from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models import db
from scheduler_service.model_helpers import add_model_helpers
from tasks import app
__author__ = 'saad'
import logging as logger

logger.basicConfig()


def init_app():
    """
    Call this method at the start of app or manager for Events/RSVPs
    :return:
    """
    app.config.from_object('config')
    add_model_helpers(db.db.Model)
    db.db.init_app(app)
    db.db.app = app
    register_error_handlers(app, logger=None)
    return app
