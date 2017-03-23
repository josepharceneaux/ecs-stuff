"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from activity_service.common.utils.models_utils import init_talent_app
# from activity_service.common.routes import GTApis
from activity_service.common.talent_config_manager import TalentConfigKeys
# from activity_service.common.talent_config_manager import load_gettalent_config
# from activity_service.common.utils.talent_ec2 import get_ec2_instance_id
# from activity_service.common.talent_flask import TalentFlask
from activity_service.common.models.db import db

app, logger = init_talent_app(__name__)

try:
    from views import api
    # from views import api_v2
    app.register_blueprint(api.mod)
    # app.register_blueprint(api_v2.api_v2, url_prefix='/v2')

    logger.info("Starting activity_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start activity_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
