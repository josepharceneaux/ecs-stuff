"""
Test cases for scheduling service
"""
# Standard imports
import json
import os
from datetime import timedelta

# Application imports
from scheduler_service import init_app
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.tests.conftest import pytest, datetime, User, user_auth, sample_user, test_domain, \
    test_org, test_culture
# Application Specific
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils

APP, celery = init_app()

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@pytest.fixture(scope='session')
def job_config_periodic(request):
    return {
        "frequency": 3600,
        'task_type': SchedulerUtils.PERIODIC,
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
def job_config_one_time(request):
    return {
        'task_type': SchedulerUtils.ONE_TIME,
        "content_type": "application/json",
        "url": "http://getTalent.com/sms/send/",
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
    returns the header which contains bearer token and content type
    :param auth_data: fixture to get access token
    :return: header dict object
    """
    header = {'Authorization': 'Bearer ' + auth_token,
              'Content-Type': 'application/json'}
    return header


@pytest.fixture(scope='function')
def auth_header_no_user(request):
    """
    returns the header which contains bearer token and content type
    :param auth_data: fixture to get access token
    :return: header dict object
    """
    secret_key_id, token = User.generate_jw_token()
    header = {'Authorization': token,
              'X-Talent-Secret-Key-ID': secret_key_id,
              'Content-Type': 'application/json'}
    return header


@pytest.fixture(scope='function')
def job_config(request, job_config_periodic):
    """
    Fixture job_config to set the start_date and end_date to current time
    :param request:
    :param job_config_periodic: fixture of hardcoded values used for testing
    :return:
    """
    temp_job_config = job_config_periodic.copy()
    start_date = datetime.utcnow() + timedelta(seconds=20)
    end_date = start_date + timedelta(days=2)
    temp_job_config['post_data'] = json.dumps(job_config_periodic['post_data'])
    temp_job_config['start_datetime'] = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    temp_job_config['end_datetime'] = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    return temp_job_config


@pytest.fixture(scope='function')
def job_config_one_time_task(request, job_config_one_time):
    """
    Fixture job_config to set the start_date and end_date to current time
    :param request:
    :param job_config_periodic: fixture of hardcoded values used for testing
    :return:
    """
    temp_job_config = job_config_one_time.copy()
    run_datetime = datetime.utcnow() + timedelta(seconds=10)
    temp_job_config['url'] = SchedulerApiUrl.TEST_TASK
    temp_job_config['post_data'] = json.dumps(job_config_one_time['post_data'])
    temp_job_config['run_datetime'] = run_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
    return temp_job_config
