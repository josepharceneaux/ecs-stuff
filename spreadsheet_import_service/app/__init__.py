__author__ = 'ufarooqi'

from flask import Flask
from flask.ext.cors import CORS
from spreadsheet_import_service.common.routes import HEALTH_CHECK
from spreadsheet_import_service.common.routes import SpreadsheetImportApi
from spreadsheet_import_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = Flask(__name__)
load_gettalent_config(app.config)

logger = app.config[TalentConfigKeys.LOGGER]

try:

    from spreadsheet_import_service.common.models.db import db
    db.init_app(app)
    db.app = app

    import api
    app.register_blueprint(api.mod, url_prefix=SpreadsheetImportApi.URL_PREFIX)

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    from spreadsheet_import_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    # Enable CORS for all origins & endpoints
    CORS(app)

    logger.info("Starting spreadsheet_import_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start spreadsheet_import_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
