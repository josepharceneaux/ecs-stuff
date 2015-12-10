"""
Test cases for scheduling service
"""
# Standard imports
import os

# Third-party imports
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

# Application imports
from scheduler_service import init_app
from scheduler_service.apscheduler_config import executors
from scheduler_service.common.tests.conftest import *
# Application Specific

APP = init_app()
APP_URL = 'http://0.0.0.0:8009'

OAUTH_SERVER = APP.config['OAUTH_SERVER_URI']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@pytest.fixture(scope='session')
def job_config(request):
    return {
        "frequency": {
            "hours": 10
        },
        'task_type': 'periodic',
        "content_type": "application/json",
        "url": "http://getTalent.com/sms/send/",
        "start_datetime": "2015-12-05T08:00:00",
        "end_datetime": "2017-01-05T08:00:00",
        "post_data": {
            "campaign_name": "SMS Campaign",
            "phone_number": "09230862348",
            "smart_list_id": 123456,
            "content": "text to be sent as sms",
        }
    }


@pytest.fixture(scope='session')
def job_config_two(request):
    return {
        'task_type': 'one_time',
        "content_type": "application/json",
        "url": "http://getTalent.com/email/send/",
        "run_datetime": "2017-05-05T08:00:00",
        "post_data": {
            "campaign_name": "Email Campaign",
            "email_id": "abc@hotmail.com",
            "smart_list_id": 123456,
            "content": "content to be sent as email",
        }
    }


@pytest.fixture(scope='function')
def auth_token(user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_row['access_token']


@pytest.fixture(scope='function')
def auth_header(request, auth_token):
    """
    returns the header which contains bearer token and content Type
    :param auth_data: fixture to get access token
    :return: header dict object
    """
    header = {'Authorization': 'Bearer ' + auth_token,
              'Content-Type': 'application/json'}
    return header

# APScheduler for creating, resuming, stopping, removing jobs


@pytest.fixture(scope='function')
def redis_jobstore_setup(request):
    """
    Sets up a Redis based job store to be used by APSCheduler
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


@pytest.fixture(scope='function')
def apscheduler_setup(request, redis_jobstore_setup):
    """
    :param request:
    :return: APScheduler object initialized with redis job store and default executor
    """

    scheduler = BackgroundScheduler(jobstore=redis_jobstore_setup, executors=executors)
    scheduler.add_jobstore(redis_jobstore_setup['redis'])
    scheduler.start()

    def resource_apscheduler_teardown():
        scheduler.shutdown()

    request.addfinalizer(resource_apscheduler_teardown)
    return scheduler
