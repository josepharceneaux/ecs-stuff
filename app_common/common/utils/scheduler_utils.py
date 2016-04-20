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
    CELERY_ROUTING_KEY = QUEUE + '_key'
    # Set the minimum frequency in seconds
    env = os.getenv(TalentConfigKeys.ENV_KEY) or 'dev'
    # For QA and production minimum frequency would be one hour
    MIN_ALLOWED_FREQUENCY = 4 if env in ['dev', 'circle'] else 3600
    MAX_MISFIRE_TIME = 60   # Max misfire of job time => 60 seconds
    # TODO--kindly add a comment against each of the following explaining why they are needed and etc
    CATEGORY_USER = 'user'
    CATEGORY_GENERAL = 'general'
    RUN_JOB_METHOD_NAME = 'run_job'
