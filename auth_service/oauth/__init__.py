__author__ = 'ufarooqi'

from auth_service.common.utils.models_utils import init_talent_app
from auth_service.common.talent_config_manager import TalentConfigKeys
from auth_service.common.migrate import db_create_all

app, logger = init_talent_app(__name__)

try:
    import views
    db_create_all()

except Exception as e:
    logger.exception("Couldn't start auth_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
