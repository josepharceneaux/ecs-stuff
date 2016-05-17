__author__ = 'ufarooqi'

from user_service.common.utils.models_utils import init_talent_app
from user_service.common.routes import UserServiceApi, GTApis
from user_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from user_service.common.utils.talent_ec2 import get_ec2_instance_id
from user_service.common.talent_flask import TalentFlask
from user_service.common.models.db import db

# TODO: clean up imports
from user_service.common.talent_api import TalentApi
from user_service.common.routes import UserServiceApi
from user_service.user_app.api.source import DomainSourceResource

app, logger = init_talent_app(__name__)

try:
    from user_service.common.redis_cache import redis_store

    # noinspection PyProtectedMember
    logger.debug("Redis connection pool: %s", repr(redis_store._redis_client.connection_pool))
    logger.debug("Info on app startup: %s", redis_store._redis_client.info())

    # Register & add resource for Domain Source API
    api = TalentApi(app)
    api.add_resource(DomainSourceResource, UserServiceApi.DOMAIN_SOURCES, endpoint='domain_sources')
    api.add_resource(DomainSourceResource, UserServiceApi.DOMAIN_SOURCE, endpoint='domain_source')

    from views import users_utilities_blueprint
    from api.users_v1 import users_blueprint
    from api.domain_v1 import domain_blueprint
    from api.roles_and_groups_v1 import groups_and_roles_blueprint

    app.register_blueprint(users_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(domain_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(users_utilities_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(groups_and_roles_blueprint, url_prefix=UserServiceApi.URL_PREFIX)

    db.create_all()
    db.session.commit()

    logger.info("Starting user_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start user_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
