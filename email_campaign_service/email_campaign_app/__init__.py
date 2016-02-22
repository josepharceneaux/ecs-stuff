"""Initialize Email campaign service app, register error handlers and register blueprint"""

from email_campaign_service.common.utils.celery_utils import init_celery_app
from email_campaign_service.common.utils.models_utils import init_talent_app
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils

app, logger = init_talent_app(__name__)

# Celery app
celery_app = init_celery_app(app, CampaignUtils.EMAIL,
                             ['email_campaign_service.modules.email_marketing'])