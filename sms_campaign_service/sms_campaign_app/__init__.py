""" Initializer for SMS Campaign Service App and Celery App"""

# Third Party
from celery import Celery

# Common Utils
from sms_campaign_service.common.utils.models_utils import init_talent_app
from sms_campaign_service.common.talent_config_manager import TalentConfigKeys

app, logger = init_talent_app(__name__)

# Celery settings
celery_app = Celery(app, broker=app.config[TalentConfigKeys.REDIS_URL_KEY],
                    backend=app.config[TalentConfigKeys.REDIS_URL_KEY],
                    include=['sms_campaign_service.modules.sms_campaign_base'])
