"""Initializer for Banner Service"""

__author__ = 'erikfarmer'

from flask.ext.redis import FlaskRedis

from banner_service.common.utils.models_utils import init_talent_app
from banner_service.common.talent_config_manager import TalentConfigKeys
# from banner_service.common.routes import ResumeApi, GTApis
# from banner_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
# from banner_service.common.utils.talent_ec2 import get_ec2_instance_id
# from banner_service.common.talent_flask import TalentFlask
# from banner_service.common.models.db import db

app, logger = init_talent_app(__name__)

try:
    redis_store = FlaskRedis(app)
    from views.v1_banners_api import banner_api_bp
    app.register_blueprint(banner_api_bp, url_prefix='/v1')

    logger.info("Starting banner_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as error:
    logger.exception("Couldn't start banner_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], error.message))