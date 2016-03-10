""" Initializer for Push Campaign Service App.
"""

# Application Specific
# TODO; this one is still using celery_utils as opposed to talent_celery???
from push_campaign_service.common.utils.celery_utils import init_celery_app
from push_campaign_service.common.utils.models_utils import init_talent_app
from push_campaign_service.common.campaign_services.campaign_utils import CampaignUtils

__author__ = 'Zohaib Ijaz <mzohaib.qc@gmail.com>'

app, logger = init_talent_app(__name__)

# Celery app
celery_app = init_celery_app(app, CampaignUtils.PUSH,
                             ['push_campaign_service.modules.push_campaign_base'])
