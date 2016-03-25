__author__ = 'ufarooqi'

from flask.ext.cors import CORS
from flask_oauthlib.provider import OAuth2Provider

from auth_service.common.utils.models_utils import init_talent_app
from auth_service.common.routes import HEALTH_CHECK, GTApis
from auth_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from auth_service.common.migrate import db_create_all
from auth_service.common.utils.talent_ec2 import get_ec2_instance_id
from auth_service.common.talent_flask import TalentFlask

app, logger = init_talent_app(__name__)

try:
    gt_oauth = OAuth2Provider()
    gt_oauth.init_app(app)

    from oauth_utilities import GetTalentOauthValidator
    gt_oauth._validator = GetTalentOauthValidator()

    db_create_all()

except Exception as e:
    logger.exception("Couldn't start auth_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
