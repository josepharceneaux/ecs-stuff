"""Initializer for Social Network Service App"""
__author__ = 'zohaib'

from itertools import chain
from flask import Flask, request

from social_network_service.common.models.db import db
from social_network_service.common.error_handling import register_error_handlers
from social_network_service.model_helpers import add_model_helpers


class CustomFlask(Flask):
    def handle_user_exception(self, e):
        """Actual method handle_user_exception uses `isinstance` to decide for proper
        error handler but it's not working as expected. So We have modified its behaviour
        by matching the name of exception.
        """
        blueprint_handlers = ()
        handlers = self.error_handler_spec.get(request.blueprint)
        if handlers is not None:
            blueprint_handlers = handlers.get(None, ())
        app_handlers = self.error_handler_spec[None].get(None, ())
        for typecheck, handler in chain(blueprint_handlers, app_handlers):
            if e.__class__.__name__ == typecheck.__name__:
                return handler(e)

        return super(CustomFlask, self).handle_user_exception(e)


flask_app = CustomFlask(__name__)
flask_app.config.from_object('social_network_service.config')
# TODO: Take this inside init_app()
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

