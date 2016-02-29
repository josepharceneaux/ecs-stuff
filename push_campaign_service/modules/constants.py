"""
Author: Zohaib Ijaz, QC-Technologies,
        Lahore, Punjab, Pakistan <mzohaib@gmail.com>

    This file contains constants used in Push Notification Service.
"""

# TODO please use same email which you are using for communication
from push_campaign_service.common.talent_config_manager import TalentConfigKeys
from push_campaign_service.push_campaign_app import app

CELERY_QUEUE = 'push_campaign'
GET_TALENT_ICON_URL = "http://cdn.designcrowd.com.s3.amazonaws.com/blog/Oct2012/" \
                      "52-Startup-Logos-2012/SLR_0040_gettalent.jpg"

ONE_SIGNAL_APP_ID = app.config[TalentConfigKeys.ONE_SIGNAL_APP_ID]
ONE_SIGNAL_REST_API_KEY = app.config[TalentConfigKeys.ONE_SIGNAL_REST_API_KEY]
PUSH_DEVICE_ID = app.config[TalentConfigKeys.PUSH_DEVICE_ID]
#TODO kindly comment what these are
DEFAULT_NOTIFICATION_OFFSET = 0
DEFAULT_NOTIFICATION_LIMIT = 50

DEFAULT_PLAYERS_OFFSET = 0
DEFAULT_PLAYERS_LIMIT = 300
