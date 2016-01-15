from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from scheduler_service.scheduler import flask_app
from redis._compat import urlparse

__author__ = 'saad'

MAX_THREAD_POOLS = 20

url = urlparse(flask_app.config['REDIS_URL'])
job_store = RedisJobStore(host=url.hostname, password=url.password)

executors = {
    'default': ThreadPoolExecutor(MAX_THREAD_POOLS)
}

jobstores = {
    'redis': job_store
}
