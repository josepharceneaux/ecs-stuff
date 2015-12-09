from apscheduler.executors.pool import ThreadPoolExecutor

__author__ = 'saad'

MAX_THREAD_POOLS = 20

executors = {
    'default': ThreadPoolExecutor(MAX_THREAD_POOLS)
}

