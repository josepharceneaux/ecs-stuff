"""Initializer for Widget App"""

__author__ = 'erikfarmer'

from flask.ext.redis import FlaskRedis

from widget_service.common.utils.models_utils import init_talent_app
from widget_service.common.routes import WidgetApi
from widget_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from widget_service.common.utils.talent_ec2 import get_ec2_instance_id
from widget_service.common.talent_flask import TalentFlask
from widget_service.common.models.db import db

app, logger = init_talent_app(__name__)

try:
    redis_store = FlaskRedis(app)

    from views import v1_api
    app.register_blueprint(v1_api.mod, url_prefix=WidgetApi.URL_PREFIX)

    logger.info("Starting widget_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as error:
    logger.exception("Couldn't start widget_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], error.message))
