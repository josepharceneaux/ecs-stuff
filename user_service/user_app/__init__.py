__author__ = 'ufarooqi'

from flask import Flask
from healthcheck import HealthCheck
from user_service.common.models.db import db
from user_service.common import common_config

app = Flask(__name__)
app.config.from_object(common_config)

logger = app.config['LOGGER']
from user_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

from views import users_utilities_blueprint
from api.users_v1 import users_blueprint
from api.domain_v1 import domain_blueprint
from api.roles_and_groups_v1 import groups_and_roles_blueprint

app.register_blueprint(users_blueprint, url_prefix='/v1')
app.register_blueprint(domain_blueprint, url_prefix='/v1')
app.register_blueprint(users_utilities_blueprint, url_prefix='/v1')
app.register_blueprint(groups_and_roles_blueprint, url_prefix='/v1')

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

db.create_all()
db.session.commit()

logger.info("Starting user_service in %s environment", app.config['GT_ENVIRONMENT'])
