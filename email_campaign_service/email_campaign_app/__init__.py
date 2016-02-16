"""Initialize Email campaign service app, register error handlers and register blueprint"""

from flask import Flask
from flask.ext.cors import CORS
from email_campaign_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from email_campaign_service.common.models.db import db
from email_campaign_service.common.error_handling import register_error_handlers
from healthcheck import HealthCheck
from email_campaign_service.common.routes import HEALTH_CHECK, GTApis

app = Flask(__name__)
load_gettalent_config(app.config)

logger = app.config[TalentConfigKeys.LOGGER]

try:
    logger.debug("Email campaign service: Register error handlers")
    register_error_handlers(app, logger)

    db.init_app(app)
    db.app = app

    # Initialize Redis Cache
    from email_campaign_service.common.redis_cache import redis_store
    redis_store.init_app(app)

    # wrap the flask app and give a healthcheck url
    health = HealthCheck(app, HEALTH_CHECK)

    from apis.email_campaigns import email_campaign_blueprint
    app.register_blueprint(email_campaign_blueprint)

    # Enable CORS for *.gettalent.com and localhost
    CORS(app, resources=GTApis.CORS_HEADERS)

    db.create_all()
    db.session.commit()

    logger.info('Starting email_campaign_service in %s environment', app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start email_campaign_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
