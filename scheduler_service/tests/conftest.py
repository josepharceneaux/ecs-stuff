"""
Test cases for scheduling service
"""
import os
import random
import string
from datetime import datetime

import pytest
from mixer._faker import faker
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import gen_salt
from mixer.backend.sqlalchemy import Mixer
from werkzeug.security import generate_password_hash
from scheduler_service import init_app

# Application Specific
from scheduler_service.common.models.db import db as _db
from scheduler_service.common.models.user import User
from scheduler_service.common.models.user import Token
from scheduler_service.common.models.user import Client
from scheduler_service.common.models.user import Domain
from scheduler_service.common.models.misc import Culture
from scheduler_service.common.models.misc import Organization



APP = init_app()
APP_URL = APP.config['APP_URL']
db_session = _db.session

OAUTH_SERVER = APP.config['OAUTH_SERVER_URI']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def get_random_word(length):
    """
    This function takes a number as an input and creates a random string of length
    specified by given number.
    :param length: int or long
    :return:
    """
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


@pytest.fixture(scope='session')
def test_client(request):
    """
    Get the test_client from the app, for the whole test session.
    This client_id and client_secret is used to create access_token for user to access APIs.
    """
    # Add test client in Client DB
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    client = Client(
        client_id=client_id,
        client_secret=client_secret
    )
    Client.save(client)

    def delete_client():
        """
        This method deletes client at the end of test session
        """
        # Client.delete(client.client_id)
        client.delete()

    request.addfinalizer(delete_client)
    return client


@pytest.fixture(scope='session')
def test_culture(request):
    mixer = Mixer(session=db_session, commit=True)
    culture = mixer.blend(Culture, description=get_random_word(20), code=get_random_word(5))

    def fin():
        """
        Delete culture at the end of test session
        """
        Culture.delete(culture.id)

    request.addfinalizer(fin)
    return culture


@pytest.fixture(scope='session')
def job_config(request):
    return {
        "frequency": {
            "day": 5,
            "hour": 6
        },
        "content_type": "application/json",
        "url": "http://getTalent.com/sms/send/",
        "start_time": "2015-12-05T08:00:00-05:00",
        "end_time": "2016-01-05T08:00:00-05:00",
        "post_data": {
            "campaign_name": "SMS Campaign",
            "phone_number": "09230862348",
            "smart_list_id": 123456,
            "content": "text to be sent as sms",
        }
    }


@pytest.fixture(scope='session')
def test_organization(request):
    """
    Creates a test organization which will be used to create domain model object
    :param request:
    :return:
    """
    organization = Organization(name=faker.nickname(), notes='')
    Organization.save(organization)
    db_session.add(organization)
    db_session.commit()

    def delete_organization():
        """
        Delete this organization at the end of test session
        """
        Organization.delete(organization.id)

    request.addfinalizer(delete_organization)

    return organization


@pytest.fixture(scope='session')
def test_domain(request, test_organization, test_culture):
    """
    Create a test domain which will be used to create user model object
    :param request:
    :param test_organization: organization fixture
    :param test_culture: culture fixture
    :return: Domain model object
    """
    now_timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    mixer = Mixer(session=db_session, commit=True)
    domain = mixer.blend(Domain, organization=test_organization, culture=test_culture,
                         name=faker.nickname(), addedTime=now_timestamp, expiration=datetime(2020, 1, 1, 0, 0, 0))

    def delete_doamin():
        """
        Delete this domain object at the end of test session
        """
        Domain.delete(domain)

    request.addfinalizer(delete_doamin)
    return domain


@pytest.fixture(scope='session')
def test_user(request, test_domain):
    """
    Create a new fresh user object for testing purposes.
    This user has no events, no credentials for any social network. We need to add that
    We will be doing that in different credentials fixture like test_meetup_credentials
    Also we will add access token record for this user in Token table
    :param request:
    :param test_domain: Domain fixture
    :return:
    """
    mixer = Mixer(session=db_session, commit=True)
    user = mixer.blend(User, domain=test_domain, firstName=get_random_word(10),
                       lastName=get_random_word(10), email=faker.email_address(),
                       password=generate_password_hash('A123456', method='pbkdf2:sha512'))

    def fin():
        """
        Delete this user object at the end of test session
        """
        User.delete(user)

    request.addfinalizer(fin)
    return user


@pytest.fixture(scope='session')
def test_token(request, test_user, test_client):
    """
    This create access token in Token table for this user so we can access API
    :param request:
    :param test_user:
    :return:
    """
    mixer = Mixer(session=db_session, commit=True)
    token = Token(user_id=test_user.id,
                  token_type='Bearer',
                  access_token=get_random_word(20),
                  refresh_token=get_random_word(20),
                  client_id=test_client.client_id,
                  expires=datetime(year=2050, month=1, day=1))
    Token.save(token)

    def fin():
        """
        Delete this token object at the end of test session
        """
        Token.delete(token)

    request.addfinalizer(fin)
    return token


@pytest.fixture(scope='session')
def auth_data(test_user, test_token):
    """
    This fixture just calls other fixtures which are required to be executed before running a test.
    and return test token for authentication
    :return: dictionary containing authentication data
    """
    token = test_token
    return token.to_json()


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
    executors = {
        'default': ThreadPoolExecutor(20)
    }
    scheduler = BackgroundScheduler(jobstore=redis_jobstore_setup, executors=executors)
    scheduler.add_jobstore(redis_jobstore_setup['redis'])
    scheduler.start()

    def resource_apscheduler_teardown():
        scheduler.shutdown()

    request.addfinalizer(resource_apscheduler_teardown)
    return scheduler
