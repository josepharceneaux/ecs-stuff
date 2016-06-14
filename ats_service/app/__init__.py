__author__ = 'Joseph Arceneaux'

from ats_service.common.utils.models_utils import init_talent_app
from ats_service.common.talent_config_manager import TalentConfigKeys
from ats_service.common.models.db import db
from ats_service.common.talent_api import TalentApi
from ats_service.common.routes import ATSServiceApi

app, logger = init_talent_app(__name__)

try:
    api = TalentApi(app=app)

    db.create_all()
    db.session.commit()

    logger.info('Starting ats-service in %s environment', app.config[TalentConfigKeys.ENV_KEY])



except Exception as e:
    logger.exception("Couldn't start ats_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
