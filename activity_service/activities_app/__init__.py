"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask
from flask.ext.cors import CORS
from activity_service.common.routes import HEALTH_CHECK
from activity_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from activity_service.common.utils.talent_ec2 import get_ec2_instance_id

app = Flask(__name__)
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]
logger.info("Starting app %s in EC2 instance %s", app.import_name, get_ec2_instance_id())

try:
    from activity_service.common.models.db import db
    db.init_app(app)
    db.app = app

    # Initialize Redis Cache
    from activity_service.common.redis_cache import redis_store
    redis_store.init_app(app)

    from views import api
    app.register_blueprint(api.mod)

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    from activity_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    # Enable CORS for all origins & endpoints
    CORS(app, resources={r"*": {"origins": [r"*.gettalent.com", "http://127.0.0.1"]}})

    logger.info("Starting activity_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start activity_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
