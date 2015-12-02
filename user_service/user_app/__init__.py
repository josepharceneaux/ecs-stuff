__author__ = 'ufarooqi'

from flask import Flask
from user_service.common.models.db import db
from user_service.common.talent_api import TalentApi
from healthcheck import HealthCheck

app = Flask(__name__)
app.config.from_object('user_service.config')

logger = app.config['LOGGER']
from user_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

from api.users_v1 import UserApi
from api.domain_v1 import DomainApi
from api.roles_and_groups_v1 import UserScopedRolesApi, UserGroupsApi, DomainGroupsApi

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

api = TalentApi(app)
api.add_resource(UserApi, "/users", "/users/<int:id>")
api.add_resource(DomainApi, "/domains", "/domains/<int:id>")
api.add_resource(UserScopedRolesApi, "/users/<int:user_id>/roles")
api.add_resource(UserGroupsApi, "/groups/<int:group_id>/users")
api.add_resource(DomainGroupsApi, "/domain/<int:domain_id>/groups", "/domain/groups/<int:group_id>")

import views

db.create_all()
db.session.commit()

logger.info("Starting user_service in %s environment", app.config['GT_ENVIRONMENT'])
