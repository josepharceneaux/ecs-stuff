"""Initializer for Resume Parsing App"""

__author__ = 'erikfarmer'
from flask.ext.redis import FlaskRedis
from flask.ext.cors import CORS
from resume_parsing_service.common.routes import ResumeApi, HEALTH_CHECK, GTApis
from resume_parsing_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from resume_parsing_service.common.utils.talent_ec2 import get_ec2_instance_id
from resume_parsing_service.common.talent_flask import TalentFlask

app = TalentFlask(__name__)
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]
logger.info("Starting app %s in EC2 instance %s", app.import_name, get_ec2_instance_id())

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

    # Enable CORS for *.gettalent.com and localhost
    CORS(app, resources=GTApis.CORS_HEADERS)

    logger.info("Starting resume_parsing_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as error:
    logger.exception("Couldn't start resume_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], error.message))
