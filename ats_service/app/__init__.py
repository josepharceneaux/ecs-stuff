__author__ = 'Joseph Arceneaux'

from ats_service.common.utils.models_utils import init_talent_app
from ats_service.common.talent_config_manager import TalentConfigKeys
from ats_service.common.models.db import db
from ats_service.common.talent_api import TalentApi
from ats_service.common.routes import ATSServiceApi
from ats_service.app.api.services import ServicesList

# from ats_service.common.models.ats import ATS

app, logger = init_talent_app(__name__)

try:
    api = TalentApi(app=app)
    api.add_resource(ServicesList, ATSServiceApi.SERVICES, endpoint='ats-services')

    db.create_all()
    db.session.commit()

    logger.info('Starting ats-service in %s environment', app.config[TalentConfigKeys.ENV_KEY])

    # ats_entry = ATS(name='WorkDay', homepage_url='https://workday.com', login_url='https://workday.com/api/login', auth_type='oauth')
    # db.session.add(ats_entry)
    # ats_entry = ATS(name='ICIMS', homepage_url='https://icims.com', login_url='https://icims.com/api/login', auth_type='basic')
    # db.session.add(ats_entry)
    # ats_entry = ATS(name='Kenexa', homepage_url='https://kenexa.com', login_url='https://kenexa.com/api/login', auth_type='oauth')
    # db.session.add(ats_entry)
    # db.session.commit()

except Exception as e:
    logger.exception("Couldn't start ats_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
