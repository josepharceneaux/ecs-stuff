__author__ = 'ufarooqi'

from flask import Flask
import api
from spreadsheet_import_service.common.models.db import db
from healthcheck import HealthCheck
from spreadsheet_import_service.common import common_config

app = Flask(__name__)
app.config.from_object(common_config)
db.init_app(app)
db.app = app

app.register_blueprint(api.mod, url_prefix='/v1')

logger = app.config['LOGGER']

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from spreadsheet_import_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

logger.info("Starting spreadsheet_import_service in %s environment", app.config['GT_ENVIRONMENT'])
