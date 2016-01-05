__author__ = 'ufarooqi'

from flask import Flask
from spreadsheet_import_service.common import common_config

app = Flask(__name__)
app.config.from_object(common_config)

logger = app.config['LOGGER']

try:

    from spreadsheet_import_service.common.models.db import db
    db.init_app(app)
    db.app = app

    import api
    app.register_blueprint(api.mod, url_prefix='/v1')

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, "/healthcheck")

    from spreadsheet_import_service.common.error_handling import register_error_handlers
    register_error_handlers(app, logger)

    logger.info("Starting spreadsheet_import_service in %s environment", app.config['GT_ENVIRONMENT'])

except Exception as e:
    logger.exception("Couldn't start spreadsheet_import_service in %s environment because: %s"
                     % (app.config['GT_ENVIRONMENT'], e.message))
