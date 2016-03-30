__author__ = 'ufarooqi'

from spreadsheet_import_service.common.utils.models_utils import init_talent_app
from spreadsheet_import_service.common.routes import GTApis
from spreadsheet_import_service.common.routes import SpreadsheetImportApi
from spreadsheet_import_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from spreadsheet_import_service.common.utils.talent_ec2 import get_ec2_instance_id
from spreadsheet_import_service.common.talent_flask import TalentFlask
from spreadsheet_import_service.common.models.db import db

app, logger = init_talent_app(__name__)

try:
    import api
    app.register_blueprint(api.mod, url_prefix=SpreadsheetImportApi.URL_PREFIX)

    logger.info("Starting spreadsheet_import_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start spreadsheet_import_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
