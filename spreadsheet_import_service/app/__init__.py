__author__ = 'ufarooqi'

from spreadsheet_import_service.common.utils.models_utils import init_talent_app
from spreadsheet_import_service.common.routes import SpreadsheetImportApi
from spreadsheet_import_service.common.talent_config_manager import TalentConfigKeys
from spreadsheet_import_service.common.talent_celery import init_celery_app

app, logger = init_talent_app(__name__)

try:

    # Instantiate Celery
    celery_app = init_celery_app(app, 'celery_spreadsheet_import_scheduler')

    import api
    app.register_blueprint(api.mod, url_prefix=SpreadsheetImportApi.URL_PREFIX)

    logger.info("Starting spreadsheet_import_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start spreadsheet_import_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
