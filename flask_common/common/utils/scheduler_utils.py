__author__ = 'basit'


import os
from ..talent_config_manager import TalentConfigKeys


class SchedulerUtils(object):
    """
    This contains constant names in scheduler_service to avoid hard coding everywhere
    """
    ONE_TIME = 'one_time'
    PERIODIC = 'periodic'
    QUEUE = 'celery_scheduler'
    # Set the minimum frequency in seconds
    env = os.getenv(TalentConfigKeys.ENV_KEY) or 'dev'
    if env in ['dev', 'circle']:
        MIN_ALLOWED_FREQUENCY = 4
    else:
        # For qa and production minimum frequency would be one hour
        MIN_ALLOWED_FREQUENCY = 3600
