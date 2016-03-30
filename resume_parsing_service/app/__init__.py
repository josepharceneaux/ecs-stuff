"""Initializer for Resume Parsing App"""

__author__ = 'erikfarmer'

from flask.ext.redis import FlaskRedis
from flask.ext.cors import CORS

from resume_parsing_service.common.utils.models_utils import init_talent_app
from resume_parsing_service.common.routes import ResumeApi, GTApis
from resume_parsing_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from resume_parsing_service.common.utils.talent_ec2 import get_ec2_instance_id
from resume_parsing_service.common.talent_flask import TalentFlask
from resume_parsing_service.common.models.db import db

app, logger = init_talent_app(__name__)

try:
    redis_store = FlaskRedis(app)

    from views import api
    app.register_blueprint(api.PARSE_MOD, url_prefix=ResumeApi.URL_PREFIX)

    logger.info("Starting resume_parsing_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as error:
    logger.exception("Couldn't start resume_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], error.message))
