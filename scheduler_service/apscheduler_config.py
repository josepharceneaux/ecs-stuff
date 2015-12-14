from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore

__author__ = 'saad'

MAX_THREAD_POOLS = 20

job_store = RedisJobStore()

executors = {
    'default': ThreadPoolExecutor(MAX_THREAD_POOLS)
}

jobstores = {
    'redis': job_store
}
