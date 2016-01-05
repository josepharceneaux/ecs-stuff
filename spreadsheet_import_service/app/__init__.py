__author__ = 'ufarooqi'

from flask import Flask
from healthcheck import HealthCheck
from spreadsheet_import_service.common.models.db import db
from spreadsheet_import_service.common.talent_config_manager import TalentConfig, ConfigKeys

app = Flask(__name__)
app.config = TalentConfig(app.config).app_config

db.init_app(app)
db.app = app

logger = app.config[ConfigKeys.LOGGER]

import api
app.register_blueprint(api.mod, url_prefix='/v1')

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from spreadsheet_import_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

logger.info("Starting spreadsheet_import_service in %s environment", app.config[ConfigKeys.ENV_KEY])
