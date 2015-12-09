from flask import Flask
from email_template_service.common.models.db import db
from api import api
from email_template_service.common.error_handling import register_error_handlers
from healthcheck import HealthCheck
from email_template_service.common import common_config

app = Flask(__name__)
app.config.from_object(common_config)
app.register_blueprint(api.mod)

logger = app.config['LOGGER']

db.init_app(app)
db.app = app

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

register_error_handlers(app, logger)

logger.info("Starting email_template_service in %s environment", app.config['GT_ENVIRONMENT'])
