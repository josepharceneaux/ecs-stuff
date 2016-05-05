
__author__ = 'basit'


import os
from ..talent_config_manager import TalentConfigKeys, TalentEnvs


class SchedulerUtils(object):
    """
    This contains constant names in scheduler_service to avoid hard coding everywhere
    """
    ONE_TIME = 'one_time'
    PERIODIC = 'periodic'
    QUEUE = 'celery_scheduler'
    CELERY_ROUTING_KEY = QUEUE + '_key'
    # Set the minimum frequency in seconds
    env = os.getenv(TalentConfigKeys.ENV_KEY) or 'dev'
    # For qa and production minimum frequency would be one hour
    MIN_ALLOWED_FREQUENCY = 3600 if os.getenv(TalentConfigKeys.ENV_KEY) == TalentEnvs.PROD else 4
    MAX_MISFIRE_TIME = 60   # Max misfire of job time => 60 seconds

    # `user` and `general` are constants for user and general job types
    CATEGORY_USER = 'user'
    CATEGORY_GENERAL = 'general'

    # Method name of default scheduler callback
    RUN_JOB_METHOD_NAME = 'run_job'
