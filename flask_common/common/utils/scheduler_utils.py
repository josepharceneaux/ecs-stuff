__author__ = 'basit'


class SchedulerUtils(object):
    """
    This contains constant names in scheduler_service to avoid hard coding everywhere
    """
    ONE_TIME = 'one_time'
    PERIODIC = 'periodic'
    QUEUE = 'celery_scheduler'
    MAX_MISFIRE_TIME = 60   # Max misfire of job time => 60 seconds

