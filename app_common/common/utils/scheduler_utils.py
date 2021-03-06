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
    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    # For QA and production minimum frequency would be one hour
    MIN_ALLOWED_FREQUENCY = 4 if env in [TalentEnvs.DEV, TalentEnvs.JENKINS] else 60
    MAX_MISFIRE_TIME = 60   # Max misfire of job time => 60 seconds

    # Redis job ids prefix for user and general job
    REDIS_SCHEDULER_USER_TASK = 'apscheduler_job_ids:user_%s'
    REDIS_SCHEDULER_GENERAL_TASK = 'apscheduler_job_ids:general_%s'
    # `user` and `general` are constants for user and general job types
    CATEGORY_USER = 'user'
    CATEGORY_GENERAL = 'general'

    # Method name of default scheduler callback
    RUN_JOB_METHOD_NAME = 'run_job'
