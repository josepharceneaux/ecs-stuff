__author__ = 'ufarooqi'

from flask import Flask
from flask.ext.cors import CORS
from flask_oauthlib.provider import OAuth2Provider
from auth_service.common.routes import HEALTH_CHECK
from auth_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from auth_service.common.migrate import db_create_all
from auth_service.common.utils.talent_ec2 import get_ec2_instance_id

app = Flask(__name__)
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]
logger.info("Starting app %s in EC2 instance %s", app.import_name, get_ec2_instance_id())

try:
    from auth_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    from auth_service.common.models.db import db
    db.init_app(app)
    db.app = app

    # wrap the flask app and give a heathcheck url

    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    gt_oauth = OAuth2Provider()
    gt_oauth.init_app(app)

    from oauth_utilities import GetTalentOauthValidator
    gt_oauth._validator = GetTalentOauthValidator()

    import views

    db_create_all()

    # Enable CORS for all origins & endpoints
    CORS(app, resources={r"*": {"origins": [r"*.gettalent.com", "127.0.0.1"]}})

    logger.info("Starting auth_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start auth_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
