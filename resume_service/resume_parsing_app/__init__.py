"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'
from flask import Flask
from resume_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
import config

app = Flask(__name__)
load_gettalent_config(app.config)
app.config.from_object(config)
logger = app.config[TalentConfigKeys.LOGGER]

try:
    from resume_service.common.models.db import db
    db.init_app(app)
    db.app = app

    from .views import api
    app.register_blueprint(api.PARSE_MOD, url_prefix='/v1')

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, "/healthcheck")

    from resume_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    logger.info("Starting resume_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start resume_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
