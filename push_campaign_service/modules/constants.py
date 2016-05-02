"""
Author: Zohaib Ijaz, QC-Technologies,
        Lahore, Punjab, Pakistan <mzohaib.qc@gmail.com>

    This file contains constants used in Push Notification Service.
"""
from push_campaign_service.push_campaign_app import app
from push_campaign_service.common.talent_config_manager import TalentConfigKeys
from push_campaign_service.common.campaign_services.campaign_utils import CampaignUtils


CELERY_QUEUE = CampaignUtils.PUSH
CAMPAIGN_REQUIRED_FIELDS = ('name', 'body_text', 'url', 'smartlist_ids')
GET_TALENT_ICON_URL = "http://cdn.designcrowd.com.s3.amazonaws.com/blog/Oct2012/" \
                      "52-Startup-Logos-2012/SLR_0040_gettalent.jpg"

ONE_SIGNAL_APP_ID = app.config[TalentConfigKeys.ONE_SIGNAL_APP_ID]
ONE_SIGNAL_REST_API_KEY = app.config[TalentConfigKeys.ONE_SIGNAL_REST_API_KEY]
ONE_SIGNAL_TEST_DEVICE_ID = 'b702183d-4541-4ec0-a977-82d2a18ff681'
