from flask.ext.cors import CORS

__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider
from auth_service.common.routes import HEALTH_CHECK
from auth_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from auth_service.common.migrate import db_create_all

app = Flask(__name__)
load_gettalent_config(app.config)

logger = app.config[TalentConfigKeys.LOGGER]

try:
    from auth_service.common.error_handling import register_error_handlers
    print "register error handlers"
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
    CORS(app)

    logger.info("Starting auth_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start auth_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
