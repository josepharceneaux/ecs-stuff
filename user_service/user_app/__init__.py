__author__ = 'ufarooqi'

from flask import Flask
from common.models.db import db
from gt_custom_restful import *
from flask_limiter import Limiter
from healthcheck import HealthCheck

app = Flask(__name__)
app.config.from_object('user_service.config')

logger = app.config['LOGGER']
from common.error_handling import register_error_handlers
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

limiter = Limiter(app, global_limits=["60 per minute"])

from api.users_v1 import UserApi
from api.domain_v1 import DomainApi

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

api = GetTalentApi(app)
api.add_resource(UserApi, "/users", "/users/<int:id>")
api.add_resource(DomainApi, "/domains", "/domains/<int:id>")

import views

db.create_all()
db.session.commit()

logger.info("Starting user_service in %s environment", app.config['GT_ENVIRONMENT'])
