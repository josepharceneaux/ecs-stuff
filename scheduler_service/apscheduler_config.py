from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from scheduler_service.scheduler import flask_app
from redis._compat import urlparse

from scheduler_service import SchedulerUtils

__author__ = 'saad'

MAX_THREAD_POOLS = 20

url = urlparse(flask_app.config['REDIS_URL'])
job_store = RedisJobStore(host=url.hostname, password=url.password)

executors = {
    'default': {'type': 'threadpool', 'max_workers': 20},
    'processpool': ProcessPoolExecutor(max_workers=5)
}

jobstores = {
    'redis': job_store
}

job_defaults = {
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.job_defaults.misfire_grace_time': str(SchedulerUtils.MAX_MISFIRE_TIME),
    'apscheduler.timezone': 'UTC',
}
