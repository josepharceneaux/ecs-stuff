""" Initializer for Push Campaign Service App.
"""
__author__ = 'Zohaib Ijaz <mzohaib.qc@gmail.com>'
# Third Party
from celery import Celery


# Application Specific
from push_campaign_service.common.utils.models_utils import init_talent_app
from push_campaign_service.common.talent_config_manager import TalentConfigKeys

app, logger = init_talent_app(__name__)

# Celery settings
celery_app = Celery(app, broker=app.config[TalentConfigKeys.REDIS_URL_KEY],
                    backend=app.config[TalentConfigKeys.REDIS_URL_KEY],
                    include=['push_campaign_service.modules.push_campaign_base'])


