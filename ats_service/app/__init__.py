__author__ = 'Joseph Arceneaux'

from ats_service.common.utils.models_utils import init_talent_app
from ats_service.common.talent_config_manager import TalentConfigKeys
from ats_service.common.talent_api import TalentApi
from ats_service.common.models.db import db
from ats_service.app.api.services_v1 import ats_service_blueprint

app, logger = init_talent_app(__name__)
app.register_blueprint(ats_service_blueprint)

try:
    db.create_all()
    db.session.commit()

    logger.info('Starting ats-service in %s environment', app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start ats_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
