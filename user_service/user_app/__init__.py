__author__ = 'ufarooqi'

from user_service.common.utils.models_utils import init_talent_app
from user_service.common.talent_config_manager import TalentConfigKeys
from user_service.common.models.db import db
from user_service.common.talent_api import TalentApi
from user_service.common.routes import UserServiceApi
from user_service.user_app.api.source import DomainSourceResource
from user_service.user_app.api.source_product import SourceProductResource

app, logger = init_talent_app(__name__)

try:
    from user_service.common.redis_cache import redis_store
    from user_service.user_app.api.domain_custom_fields import DomainCustomFieldsResource
    from user_service.user_app.api.domain_areas_of_interest import DomainAreaOfInterestResource
    from user_service.user_app.api.domain_cf_categories import DomainCustomFieldCategoriesResource
    from user_service.user_app.api.domain_tags import DomainTagResource

    # noinspection PyProtectedMember
    logger.debug("Redis connection pool: %s", repr(redis_store._redis_client.connection_pool))
    logger.debug("Info on app startup: %s", redis_store._redis_client.info())

    api = TalentApi(app)

    # Register & add resource for Domain Source API
    api.add_resource(DomainSourceResource, UserServiceApi.DOMAIN_SOURCES, endpoint='domain_sources')
    api.add_resource(DomainSourceResource, UserServiceApi.DOMAIN_SOURCE, endpoint='domain_source')

    # Register & add resource for Source Product
    api.add_resource(SourceProductResource, UserServiceApi.SOURCE_PRODUCTS, endpoint='source_products')
    api.add_resource(SourceProductResource, UserServiceApi.SOURCE_PRODUCT, endpoint='source_product')

    # Domain area(s) of interest
    api.add_resource(DomainAreaOfInterestResource, UserServiceApi.DOMAIN_AOIS, endpoint='domain_aois')
    api.add_resource(DomainAreaOfInterestResource, UserServiceApi.DOMAIN_AOI, endpoint='domain_aoi')

    # Register & add resource for Domain Custom Field API
    api.add_resource(DomainCustomFieldsResource, UserServiceApi.DOMAIN_CUSTOM_FIELDS, endpoint='domain_custom_fields')
    api.add_resource(DomainCustomFieldsResource, UserServiceApi.DOMAIN_CUSTOM_FIELD, endpoint='domain_custom_field')

    # Domain custom field categories
    api.add_resource(DomainCustomFieldCategoriesResource,
                     UserServiceApi.DOMAIN_CUSTOM_FIELD_CATEGORIES,
                     endpoint='domain_custom_field_categories')
    api.add_resource(DomainCustomFieldCategoriesResource,
                     UserServiceApi.DOMAIN_CUSTOM_FIELD_CATEGORY,
                     endpoint='domain_custom_field_category')

    # Domain Tags Resource
    api.add_resource(DomainTagResource, UserServiceApi.DOMAIN_TAGS, endpoint='domain_tags')

    from views import users_utilities_blueprint
    from api.users_v1 import users_blueprint
    from api.domain_v1 import domain_blueprint
    from api.test_setup import test_setup_blueprint
    from api.roles_and_groups_v1 import groups_and_roles_blueprint

    app.register_blueprint(users_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(domain_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(users_utilities_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(groups_and_roles_blueprint, url_prefix=UserServiceApi.URL_PREFIX)
    app.register_blueprint(test_setup_blueprint, url_prefix=UserServiceApi.URL_PREFIX)

    db.create_all()
    db.session.commit()

    logger.info("Starting user_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start user_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
