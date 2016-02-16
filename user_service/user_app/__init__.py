
__author__ = 'ufarooqi'

from flask import Flask
from flask.ext.cors import CORS
from user_service.common.routes import UserServiceApi, HEALTH_CHECK, GTApis
from user_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from user_service.common.utils.talent_ec2 import get_ec2_instance_id

app = Flask(__name__)
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]
logger.info("Starting app %s in EC2 instance %s", app.import_name, get_ec2_instance_id())

try:
    from user_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    from user_service.common.models.db import db
    db.init_app(app)
    db.app = app

    from user_service.common.redis_cache import redis_store
    redis_store.init_app(app)
    # noinspection PyProtectedMember
    logger.debug("Redis connection pool: %s", repr(redis_store._redis_client.connection_pool))
    logger.debug("Info on app startup: %s", redis_store._redis_client.info())

    from views import users_utilities_blueprint
    from api.users_v1 import users_blueprint
    from api.domain_v1 import domain_blueprint
    from api.roles_and_groups_v1 import groups_and_roles_blueprint

    app.register_blueprint(users_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(domain_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(users_utilities_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(groups_and_roles_blueprint, url_prefix=UserServiceApi.URL_PREFIX)

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    db.create_all()
    db.session.commit()

    # Enable CORS for *.gettalent.com and localhost
    CORS(app, resources=GTApis.CORS_HEADERS)

    logger.info("Starting user_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start user_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))


