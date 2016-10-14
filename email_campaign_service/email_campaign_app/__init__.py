"""Initialize Email campaign service app, register error handlers and register blueprint"""

from flask.ext.cache import Cache
from email_campaign_service.common.models.db import db
from email_campaign_service.common.talent_celery import init_celery_app
from email_campaign_service.common.utils.models_utils import init_talent_app
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils

app, logger = init_talent_app(__name__)

# Instantiate Flask-Cache object
cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': app.config['REDIS_URL']})

# Celery app
celery_app = init_celery_app(app, CampaignUtils.EMAIL,
                             ['email_campaign_service.modules.email_marketing',
                              'email_campaign_service.modules.utils',
                              'email_campaign_service.modules.email_clients'])
