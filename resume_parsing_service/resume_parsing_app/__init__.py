"""Initializer for Resume Parsing App"""

__author__ = 'erikfarmer'
from flask import Flask
from flask.ext.redis import FlaskRedis
from resume_parsing_service.common.routes import ResumeApi, HEALTH_CHECK
from resume_parsing_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = Flask(__name__)
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]

try:
    from resume_parsing_service.common.models.db import db
    db.init_app(app)
    db.app = app

    redis_store = FlaskRedis(app)

    from views import api
    app.register_blueprint(api.PARSE_MOD, url_prefix=ResumeApi.URL_PREFIX)

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    from resume_parsing_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    logger.info("Starting resume_parsing_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as error:
    logger.exception("Couldn't start resume_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], error.message))
