"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask

app = Flask(__name__)
app.config.from_object('activity_service.config')

logger = app.config['LOGGER']

try:
    from activity_service.common.models.db import db
    db.init_app(app)
    db.app = app

    from views import api
    app.register_blueprint(api.mod)

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, "/healthcheck")

    from activity_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    logger.info("Starting activity_service in %s environment", app.config['GT_ENVIRONMENT'])

except Exception as e:
    logger.exception("Couldn't start activity_service in %s environment because: %s"
                     % (app.config['GT_ENVIRONMENT'], e.message))
