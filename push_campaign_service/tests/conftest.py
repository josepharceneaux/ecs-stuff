"""
Author: Zohaib Ijaz <mzohaib.qc@gmail.com>

This module contains fixtures to be used in tests for push campaign service.

Most of the fixtures are created twice. First one with 'user_first' as owner and those that
are postfix with  '_2' are owned by 'user_second'. 'user_first' belongs to domain 1 and
'user_second' belongs to another domain say domain 2.

A user can update or delete objects that  are owned by a user that is from same domain. so there
are some fixture that are postfix with '_with_same_domain', actually belong to domain 1
but maybe some other user.

"""
import time
from datetime import datetime

import requests

from push_campaign_service.push_campaign_app.app import app
from app_common.common.utils.handy_functions import add_role_to_test_user
from push_campaign_service.common.models.misc import UrlConversion
# from push_campaign_service.common.tests.conftest import (user_auth, first_group, sample_user,
#                                                          sample_user_2, user_from_diff_domain,
#                                                          test_domain, domain_first,
#                                                          test_org, test_domain_2,
#                                                          second_group, domain_second,
#                                                          user_first, user_second, user_same_domain,
#                                                          access_token_first, access_token_second,
#                                                          access_token_same, sample_client, talent_pool)
from push_campaign_service.common.routes import (PushCampaignApiUrl, SchedulerApiUrl,
                                                 CandidatePoolApiUrl, CandidateApiUrl,
                                                 UserServiceApiUrl)
from push_campaign_service.common.models.db import db

from push_campaign_service.tests.test_utilities import (invalid_data_test,
                                                        unauthorize_test,
                                                        missing_key_test,
                                                        send_request, OK,
                                                        NOT_FOUND,
                                                        INVALID_USAGE, FORBIDDEN, add_roles,
                                                        remove_roles)
from push_campaign_service.common.models.smartlist import Smartlist
from push_campaign_service.common.models.candidate import (Candidate,
                                                           CandidateDevice,
                                                           CandidateEmail)


from push_campaign_service.common.models.push_campaign import (PushCampaign,
                                                               PushCampaignSmartlist,
                                                               PushCampaignSendUrlConversion)

from faker import Faker
import pytest

from push_campaign_service.modules.constants import PUSH_DEVICE_ID
from push_campaign_service.push_campaign_app import logger
from push_campaign_service.tests.test_utilities import (generate_campaign_data, send_request,
                                                        generate_campaign_schedule_data, SLEEP_TIME,
                                                        create_smart_list)
import ConfigParser

CONFIG_FILE_NAME = "test.cfg"
LOCAL_CONFIG_PATH = "/home/zohaib/.talent/%s" % CONFIG_FILE_NAME
ROLES = ['CAN_ADD_TALENT_POOLS', 'CAN_GET_TALENT_POOLS', 'CAN_DELETE_TALENT_POOLS',
         'CAN_ADD_TALENT_POOLS_TO_GROUP', 'CAN_ADD_CANDIDATES', 'CAN_GET_CANDIDATES',
         'CAN_DELETE_CANDIDATES', 'CAN_ADD_TALENT_PIPELINE_SMART_LISTS',
         'CAN_DELETE_TALENT_PIPELINE_SMART_LISTS']


class TestConfigParser(ConfigParser.ConfigParser):

    def to_dict(self):
        sections = dict(self._sections)
        for k in sections:
            sections[k] = dict(self._defaults, **sections[k])
            sections[k].pop('__name__', None)
        return sections


fake = Faker()

config = TestConfigParser()
config.read(LOCAL_CONFIG_PATH)
print(config.to_dict())

test_config = config.to_dict()


@pytest.fixture()
def token_first(request):
    info = test_config['USER_FIRST']
    data = {'client_id': info['client_id'],
            'client_secret': info['client_secret'],
            'username': info['username'],
            'password': info['password'],
            'grant_type': 'password'
            }
    resp = requests.post('http://localhost:8001/v1/oauth2/token', data=data)
    assert resp.status_code == 200
    token = resp.json()['access_token']
    return token


@pytest.fixture()
def token_same_domain(request):
    info = test_config['USER_SAME_DOMAIN']
    data = {'client_id': info['client_id'],
            'client_secret': info['client_secret'],
            'username': info['username'],
            'password': info['password'],
            'grant_type': 'password'
            }
    resp = requests.post('http://localhost:8001/v1/oauth2/token', data=data)
    assert resp.status_code == 200
    token = resp.json()['access_token']
    return token


@pytest.fixture()
def token_second(request):
    info = test_config['USER_SECOND']
    data = {'client_id': info['client_id'],
            'client_secret': info['client_secret'],
            'username': info['username'],
            'password': info['password'],
            'grant_type': 'password'
            }
    resp = requests.post('http://localhost:8001/v1/oauth2/token', data=data)
    assert resp.status_code == 200
    token = resp.json()['access_token']
    return token


@pytest.fixture()
def user_first(request, token_first):
    """
    This fixture will be used to send request for push campaigns
    :param request: request object
    :param token_first: auth token for first user
    :return: user dictionary object
    """
    user_id = test_config['USER_FIRST']['user_id']
    response = send_request('get', UserServiceApiUrl.USER % user_id, token_first)
    assert response.status_code == 200
    user = response.json()['user']
    add_roles(user['id'], ROLES, token_first)

    def tear_down():
        remove_roles(user['id'], ROLES, token_first)

    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def user_second(request, token_second):
    """
    This fixture will be used to send request for push campaigns to test same domain functionality
    :param request: request object
    :param access_token_second: auth token for first user
    :param user_second: second user for tests
    :return: user dictionary object
    """
    user_id = test_config['USER_SECOND']['user_id']
    response = send_request('get', UserServiceApiUrl.USER % user_id, token_second)
    assert response.status_code == 200
    user = response.json()['user']
    add_roles(user['id'], ROLES, token_second)

    def tear_down():
        remove_roles(user['id'], ROLES, token_second)

    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def user_same_domain(request, token_same_domain):
    """
    This fixture will be used to send request for push campaigns
    :param request: request object
    :param access_token_same: auth token for a user from same domain as of user first
    :param user_same_domain: user from same domain as of user first
    :return: user dictionary object
    """
    user_id = test_config['USER_SAME_DOMAIN']['user_id']
    response = send_request('get', UserServiceApiUrl.USER % user_id, token_same_domain)
    assert response.status_code == 200
    user = response.json()['user']
    add_roles(user['id'], ROLES, token_same_domain)

    def tear_down():
        remove_roles(user['id'], ROLES, token_same_domain)

    request.addfinalizer(tear_down)
    return user


@pytest.fixture(scope='function')
def campaign_data(request):
    """ Generate random data for a push campaign
    """
    data = generate_campaign_data()

    def tear_down():
        if 'id' in data and 'token' in data:
            response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % data['id'], data['token'])
            assert response.status_code in [OK, NOT_FOUND]
    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_in_db(request, token_first, smartlist_first, campaign_data):
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_first['id']]
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token_first, data)
    assert response.status_code == 201
    id = response.json()['id']
    data['id'] = id

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % id, token_first)
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return data

@pytest.fixture()
def campaign_in_db_multiple_smartlists(request, token_first, smartlist_first, campaign_data,
                                       smartlist_same_doamin):
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_first['id'], smartlist_same_doamin['id']]
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token_first, data)
    assert response.status_code == 201
    id = response.json()['id']
    data['id'] = id

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % id, token_first)
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return data

@pytest.fixture()
def campaign_in_db_second(request, token_second, smartlist_second, campaign_data):
    """
    This fixture creates a push campaign in database for sample_user
    :param request:
    :param token_second: token for user_second
    :param smartlist_second: test smartlist associated to user_second
    :param campaign_data: dictionary containing campaign data
    :return:
    """
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_second['id']]
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token_second, data)
    assert response.status_code == 201
    id = response.json()['id']
    data['id'] = id

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % id,
                                token_second, data)
        assert response.status_code == OK

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_blast(token_first, campaign_in_db, candidate_device_first):
    response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db['id'], token_first)
    logger.info(response.content)
    assert response.status_code == 200
    time.sleep(SLEEP_TIME)
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
    assert response.status_code == OK
    blasts = response.json()['blasts']
    assert len(blasts) == 1
    blast = blasts[0]
    return blast


@pytest.fixture(scope='function')
def smartlist_first(request, token_first, candidate_first, candidate_device_first):
    """
    This fixture associates a smartlist with push campaign object
    :param request: request object
    :param candidate_first: candidate object
    :param token_first: access token for user_first
    :return: smartlist id
    """
    data = {
        'candidate_ids': [candidate_first['id']],
        'name': fake.word()
    }
    response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, token_first, data=data)
    assert response.status_code == 201
    smartlist = response.json()['smartlist']
    smartlist_id = smartlist['id']

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.SMARTLIST % smartlist_id, token_first)
        assert response.status_code == OK
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_second(request, user_second, candidate_second, candidate_device_second, token_second):
    """
    This fixture associates a smartlist with push campaign object
    :param request: request object
    :param sample_user: test user to use pai
    :param test_candidate: candidate object
    :param test_candidate_device: device associated with candidate
    :param campaign_in_db: push campaign obj
    :return: smartlist object
    """
    data = {
        'candidate_ids': [candidate_second['id']],
        'name': fake.word()
    }
    response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, token_second, data=data)
    assert response.status_code == 201
    smartlist = response.json()['smartlist']
    smartlist_id = smartlist['id']

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.SMARTLIST % smartlist_id, token_second)
        assert response.status_code == OK
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_same_doamin(request, user_same_domain, token_same_domain, candidate_same_domain, candidate_device_same_domain, campaign_in_db):
    """
    This fixture is similar to "test_smartlist".
    it just associates another smartlist with given campaign
    :param request:
    :param sample_user:
    :param test_candidate:
    :param test_candidate_device:
    :param campaign_in_db:
    :return: smaertlist object
    """
    data = {
        'candidate_ids': [candidate_same_domain['id']],
        'name': fake.word()
    }
    response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, token_same_domain, data=data)
    assert response.status_code == 201
    smartlist = response.json()['smartlist']
    smartlist_id = smartlist['id']

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.SMARTLIST % smartlist_id, token_same_domain)
        assert response.status_code == OK
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def campaign_blasts(campaign_in_db, token_first, candidate_device_first):
    """
    This fixture hits Push campaign api to send campaign which in turn creates blast.
    At the end just return total blast created.
    :param test_smartlist: smartlist associated with campaign
    :param campaign_in_db: push campaign object
    :param token_first: auth token
    """

    blasts_counts = 3
    for num in range(blasts_counts):
        response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db['id'], token_first)
        assert response.status_code == 200
    time.sleep(SLEEP_TIME)
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
    assert response.status_code == 200
    return response.json()['blasts']


@pytest.fixture()
def schedule_a_campaign(request, smartlist_first, campaign_in_db, token_first):
    """
    This fixture sends a POST request to Push campaign api to schedule this campaign,
    which will be further used in tests.
    :param request: request object
    :param smartlist_first: smartlist associated with campaign
    :param campaign_in_db: push campaign which is to be scheduled
    :return data: schedule data
    :rtype data: dict
    """
    task_id = None
    data = generate_campaign_schedule_data()
    response = send_request('post', PushCampaignApiUrl.SCHEDULE % campaign_in_db['id'], token_first, data)
    assert response.status_code == 200
    response = response.json()
    task_id = response['task_id']

    def fin():
        send_request('delete', SchedulerApiUrl.TASK % task_id, token_first)

    request.addfinalizer(fin)
    return data


@pytest.fixture()
def url_conversion(request, token_first, campaign_in_db, smartlist_first, candidate_device_first):
    """
    This method Sends a campaign and then returns a UrlConversion object
    associated with this campaign.
    :return:
    """
    response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db['id'], token_first)
    assert response.status_code == 200
    time.sleep(SLEEP_TIME)  # had to add this as sending process runs on celery
    # get campaign blast
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
    assert response.status_code == 200
    blasts = response.json()['blasts']
    assert len(blasts) == 1
    blast_id = blasts[0]['id']
    # get campaign sends
    response = send_request('get', PushCampaignApiUrl.BLAST_SENDS
                            % (campaign_in_db['id'], blast_id), token_first)
    assert response.status_code == 200
    sends = response.json()['sends']
    # get if of record of sms_campaign_send_url_conversion for this campaign
    assert len(sends) == 1
    campaign_send = sends[0]
    response = send_request('get', PushCampaignApiUrl.URL_CONVERSION_BY_SEND_ID % campaign_send['id'], token_first)
    assert response.status_code == 200
    url_conversion = response.json()['url_conversion']

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.URL_CONVERSION % url_conversion['id'], token_first)
        assert response.status_code == 200

    request.addfinalizer(tear_down)
    return url_conversion


@pytest.fixture(scope='function')
def talent_pool(request, token_first):
    """
    This fixture created a test candidate using sample user and it will be deleted
    after test has run.
    """
    data = {
        "talent_pools": [
            {
                "name": fake.word(),
                "description": fake.paragraph()
            }
        ]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOLS, token_first, data=data)
    assert response.status_code == 200
    talent_pool_id = response.json()['talent_pools'][0]

    response = send_request('get', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_first)
    assert response.status_code == 200
    talent_pool = response.json()['talent_pool']
    data = {
        "talent_pools": [talent_pool_id]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOL_GROUP % 1, token_first, data=data)
    assert response.status_code == 200

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_first)
        assert response.status_code == 200

    request.addfinalizer(tear_down)
    return talent_pool


@pytest.fixture(scope='function')
def talent_pool_second(request, user_second, token_second):
    """
    This fixture created a test talent pool that is associated to user_second of domain_second
    """
    data = {
        "talent_pools": [
            {
                "name": fake.word(),
                "description": fake.paragraph()
            }
        ]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOLS, token_second, data=data)
    assert response.status_code == 200
    talent_pool_id = response.json()['talent_pools'][0]

    response = send_request('get', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_second)
    assert response.status_code == 200
    talent_pool = response.json()['talent_pool']
    data = {
        "talent_pools": [talent_pool_id]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOL_GROUP % 2, token_second, data=data)
    assert response.status_code == 200

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_second)
    assert response.status_code == 200

    request.addfinalizer(tear_down)
    return talent_pool


@pytest.fixture(scope='function')
def candidate_first(request, user_first, talent_pool, token_first):
    """
    This fixture created a test candidate using sample user and it will be deleted
    after test has run.
    """
    data = {
        "candidates": [
            {
                "first_name": fake.first_name(),
                "middle_name": fake.user_name(),
                "last_name": fake.last_name(),
                "talent_pool_ids": {
                    "add": [talent_pool['id']]
                },
                "emails": [
                    {
                        "label": "Primary",
                        "address": fake.email(),
                        "is_default": True
                    }
                ]
            }

        ]
    }
    response = send_request('post', CandidateApiUrl.CANDIDATES, token_first, data=data)
    assert response.status_code == 201
    candidate_id = response.json()['candidates'][0]['id']
    response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token_first)
    assert response.status_code == OK
    candidate = response.json()['candidate']

    def tear_down():
        response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token_first)
        assert response.status_code == OK

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def candidate_same_domain(request, user_same_domain, talent_pool, token_same_domain):
    """
    This fixture created a test candidate using sample user and it will be deleted
    after test has run.
    """
    data = {
        "candidates": [
            {
                "first_name": fake.first_name(),
                "middle_name": fake.user_name(),
                "last_name": fake.last_name(),
                "talent_pool_ids": {
                    "add": [talent_pool['id']]
                },
                "emails": [
                    {
                        "label": "Primary",
                        "address": fake.email(),
                        "is_default": True
                    }
                ]
            }

        ]
    }
    response = send_request('post', CandidateApiUrl.CANDIDATES, token_same_domain, data=data)
    assert response.status_code == 201
    candidate_id = response.json()['candidates'][0]['id']
    response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token_same_domain)
    assert response.status_code == OK
    candidate = response.json()['candidate']

    def tear_down():
        response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token_same_domain)
        assert response.status_code == OK

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def candidate_second(request, token_second, talent_pool_second):
    """
    This fixture created a test candidate using for domain 2 and it will be deleted
    after test has run.
    """
    # with app.app_context():
    #         add_role_to_test_user(user_first, ['CAN_ADD_CANDIDATES'])

    data = {
        "candidates": [
            {
                "first_name": fake.first_name(),
                "middle_name": fake.user_name(),
                "last_name": fake.last_name(),
                "talent_pool_ids": {
                    "add": [talent_pool_second['id']]
                },
                "emails": [
                    {
                        "label": "Primary",
                        "address": fake.email(),
                        "is_default": True
                    }
                ]
            }

        ]
    }
    response = send_request('post', CandidateApiUrl.CANDIDATES, token_second, data=data)
    assert response.status_code == 201
    candidate_id = response.json()['candidates'][0]['id']
    response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token_second)
    assert response.status_code == OK
    candidate = response.json()['candidate']

    def tear_down():
        response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token_second)
        assert response.status_code == OK

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def candidate_device_first(request,token_first, candidate_first):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_first['id'], token_first,
                            data=data)
    response.status_code == 201
    response = send_request('get', CandidateApiUrl.DEVICES % candidate_first['id'], token_first)
    assert response.status_code == OK
    devices = response.json()['devices']
    assert len(devices) == 1
    return devices[0]


@pytest.fixture(scope='function')
def candidate_device_same_domain(request, token_same_domain, candidate_same_domain):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_same_domain['id'],
                            token_same_domain,
                            data=data)
    response.status_code == 201
    response = send_request('get', CandidateApiUrl.DEVICES % candidate_same_domain['id'],
                            token_same_domain)
    assert response.status_code == OK
    devices = response.json()['devices']
    assert len(devices) == 1
    return devices[0]


@pytest.fixture(scope='function')
def candidate_device_second(request, candidate_second):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    """
    device = CandidateDevice(candidate_id=candidate_second['id'],
                             one_signal_device_id=PUSH_DEVICE_ID,
                             registered_at=datetime.utcnow())
    CandidateDevice.save(device)

    return device



