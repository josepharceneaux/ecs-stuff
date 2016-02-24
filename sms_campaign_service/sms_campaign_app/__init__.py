""" Initializer for SMS Campaign Service App and Celery App"""

# Common Utils
from sms_campaign_service.common.utils.celery_utils import init_celery_app
from sms_campaign_service.common.utils.models_utils import init_talent_app
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignUtils

app, logger = init_talent_app(__name__)

# Celery app
celery_app = init_celery_app(app, CampaignUtils.SMS,
                             ['sms_campaign_service.modules.sms_campaign_base'])
