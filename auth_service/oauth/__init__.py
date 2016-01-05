__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider
from auth_service.common import common_config

app = Flask(__name__)
app.config.from_object(common_config)

logger = app.config['LOGGER']

try:
    from auth_service.common.error_handling import register_error_handlers
    print "register error handlers"
    register_error_handlers(app, logger)

    from auth_service.common.models.db import db
    db.init_app(app)
    db.app = app

    # wrap the flask app and give a heathcheck url

    from healthcheck import HealthCheck
    health = HealthCheck(app, "/healthcheck")

    gt_oauth = OAuth2Provider()
    gt_oauth.init_app(app)

    from oauth_utilities import GetTalentOauthValidator
    gt_oauth._validator = GetTalentOauthValidator()

    import views

    db.create_all()
    db.session.commit()

    logger.info("Starting auth_service in %s environment", app.config['GT_ENVIRONMENT'])

except Exception as e:
    logger.exception("Couldn't start auth_service in %s environment because: %s"
                     % (app.config['GT_ENVIRONMENT'], e.message))
