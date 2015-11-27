"""
Test cases for scheduling service
"""
from scheduler_service.common.models.db import db
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import pytest
from redis import Redis

__author__ = 'saad'


"""
Redis db for data storage
"""

db_session = db.session

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='session')
def resource_redis_db_setup(request):
    app = Flask(__name__)
    redis = Redis(app, app.config['REDIS_URL'])

    def resource_redis_db_teardown():
        redis.flushdb()
        pass
    request.addfinalizer(resource_redis_db_teardown)
    return redis


"""
APScheduler for creating, resuming, stopping, removings jobs
"""


@pytest.fixture(scope='session')
def resource_redis_jobstore_setup(request):
    """
    :param request:
    :return: redis jobstore dictionary object
    {
        'redis': job_store_object
    }
    """
    jobstore = {
        'redis': RedisJobStore()
    }

    def resource_redis_jobstore_teardown():
        jobstore['redis'].remove_all_jobs()

    request.addfinalizer(resource_redis_jobstore_teardown)
    return jobstore


@pytest.fixture(scope='session')
def resource_apscheduler_setup(request, resource_redis_jobstore_setup):
    """
    :param request:
    :return: APScheduler object initialized with redis job store and default executor
    """
    executors = {
        'default': ThreadPoolExecutor(20)
    }
    scheduler = BackgroundScheduler(jobstore=resource_redis_jobstore_setup, executors=executors)
    scheduler.add_jobstore(resource_redis_jobstore_setup['redis'])
    scheduler.start()

    def resource_apscheduler_teardown():
        scheduler.shutdown()

    request.addfinalizer(resource_apscheduler_teardown)
    return scheduler


