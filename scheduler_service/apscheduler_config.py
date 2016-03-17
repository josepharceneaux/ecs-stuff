from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from scheduler_service.scheduler import flask_app
from redis._compat import urlparse

from scheduler_service import SchedulerUtils, TalentConfigKeys

__author__ = 'saad'

MAX_THREAD_POOLS = 12

url = urlparse(flask_app.config[TalentConfigKeys.REDIS_URL_KEY])
job_store = RedisJobStore(host=url.hostname, password=url.password)

executors = {
    'default': ThreadPoolExecutor(MAX_THREAD_POOLS),
    'processpool': ProcessPoolExecutor(max_workers=10)
}

jobstores = {
    'redis': job_store
}

job_defaults = {
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.job_defaults.misfire_grace_time': str(SchedulerUtils.MAX_MISFIRE_TIME),
    'apscheduler.timezone': 'UTC'
}
