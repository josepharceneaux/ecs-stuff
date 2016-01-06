__author__ = 'ufarooqi'

from flask import Flask
from user_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = Flask(__name__)
load_gettalent_config(app.config)

logger = app.config[TalentConfigKeys.LOGGER]

try:
    from user_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    from user_service.common.models.db import db
    db.init_app(app)
    db.app = app

    from user_service.common.redis_cache import redis_store
    redis_store.init_app(app)

    from views import users_utilities_blueprint
    from api.users_v1 import users_blueprint
    from api.domain_v1 import domain_blueprint
    from api.roles_and_groups_v1 import groups_and_roles_blueprint

    app.register_blueprint(users_blueprint, url_prefix='/v1')
    app.register_blueprint(domain_blueprint, url_prefix='/v1')
    app.register_blueprint(users_utilities_blueprint, url_prefix='/v1')
    app.register_blueprint(groups_and_roles_blueprint, url_prefix='/v1')

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, "/healthcheck")

    db.create_all()
    db.session.commit()

    logger.info("Starting user_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start user_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))


