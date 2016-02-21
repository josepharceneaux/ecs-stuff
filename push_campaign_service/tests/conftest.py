"""
Author: Zohaib Ijaz <mzohaib.qc@gmail.com>

This module contains fixtures to be used in tests for push campaign service.

Most of the fixtures are created twice. First one with 'user_first' as owner and those that
are postfix with  '_second' are owned by 'user_second'. 'user_first' belongs to domain 1 and
'user_second' belongs to another domain say domain 2.

A user can update or delete objects that  are owned by a user that is from same domain. so there
are some fixture that are postfix with '_same_domain', actually belong to domain 1
but maybe some other user.

"""
import time
import pytest
from faker import Faker

from push_campaign_service.push_campaign_app import logger
from push_campaign_service.common.tests.conftest import randomword
from push_campaign_service.modules.constants import PUSH_DEVICE_ID
from push_campaign_service.common.test_config_manager import load_test_config
from push_campaign_service.common.tests.api_conftest import (token_first, token_same_domain,
                                                             token_second, user_first,
                                                             user_same_domain, user_second)
from push_campaign_service.common.routes import (PushCampaignApiUrl, SchedulerApiUrl,
                                                 CandidatePoolApiUrl, CandidateApiUrl)
from push_campaign_service.tests.test_utilities import (generate_campaign_data, send_request,
                                                        generate_campaign_schedule_data, SLEEP_TIME,
                                                        OK, NOT_FOUND)


CONFIG_FILE_NAME = "test.cfg"
LOCAL_CONFIG_PATH = "/home/zohaib/.talent/%s" % CONFIG_FILE_NAME

fake = Faker()
test_config = load_test_config()


@pytest.fixture(scope='function')
def campaign_data(request):
    """
    This fixtures returns random campaign data which includes name of campaign,
    body_text and url for campaign
    :param request: request object
    :return: campaign data dict
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
    """
    This fixture creates a campaign in database by hitting push campaign service api
    :param request: request object
    :param token_first: authentication token for user_first
    :param smartlist_first: smartlist dict object
    :param campaign_data: data to create campaign
    :return:
    """
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
    """
    This fixtures creates a campaign which is associated with multiple two smartlist,
    one th
    :param request:
    :param token_first: at belongs to same users, and one created by other
    user from same domain
    :param smartlist_first: smartlist dict object owned by user_first
    :param smartlist_same_doamin: smartlist dict object owned by user_same_domain
    :param campaign_data: dict data to create campaign
    :return:
    """
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
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_blast(token_first, campaign_in_db, candidate_device_first):
    """
    This fixture creates a campaign blast for given campaign by sending a campaign
    :param token_first: authentication token
    :param campaign_in_db: campaign dict object
    :param candidate_device_first: candidate device dict object
    :return:
    """
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
    :param candidate_device_first: candidate device object
    :return: smartlist objects (dict)
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
        assert response.status_code in [OK, NOT_FOUND]
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_second(request, user_second, candidate_second, candidate_device_second, token_second):
    """
    This fixture associates a smartlist with push campaign object
    :param request: request object
    :param user_second: user from a different domain
    :param candidate_second: candidate object
    :param candidate_device_second: device associated with candidate
    :param token_second: access token for user_second
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
        assert response.status_code in [OK, NOT_FOUND]
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_same_doamin(request, user_same_domain, token_same_domain, candidate_same_domain, candidate_device_same_domain, campaign_in_db):
    """
    This fixture is similar to "test_smartlist".
    it just associates another smartlist with given campaign
    :param request:
    :param user_same_domain: user from same domain as of user_first, to test
     same domain functionality
    :param token_same_domain: auth token for user_same_domain
    :param candidate_same_domain: candidate from domain as of user_same_domain
    :param campaign_in_db:
    :param candidate_device_same_domain: device associated to candidate_same_domain
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
        assert response.status_code in [OK, NOT_FOUND]
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def campaign_blasts(campaign_in_db, token_first, candidate_device_first):
    """
    This fixture hits Push campaign api to send campaign which in turn creates blast.
    At the end just return list of blasts created
    :param candidate_device_first: device associated to first candidate
    :param campaign_in_db: push campaign object
    :param token_first: auth token
    """

    blasts_counts = 3
    for num in range(blasts_counts):
        response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db['id'], token_first)
        assert response.status_code == OK
    time.sleep(SLEEP_TIME)
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
    assert response.status_code == OK
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
        response = send_request('delete', SchedulerApiUrl.TASK % task_id, token_first)
        assert response.status_code in [OK, NOT_FOUND]
    request.addfinalizer(fin)
    return data


@pytest.fixture()
def url_conversion(request, token_first, campaign_in_db, smartlist_first, candidate_device_first):
    """
    This method Sends a campaign and then returns a UrlConversion object
    associated with this campaign.
    :param token_first: authentication token
    :param campaign_in_db: campaign dict object
    :param smartlist_first: smarlist dict object associated with campaign
    :param candidate_device_first: candidate device dict object
    :return:
    """
    response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db['id'], token_first)
    assert response.status_code == OK
    time.sleep(SLEEP_TIME)  # had to add this as sending process runs on celery
    # get campaign blast
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
    assert response.status_code == OK
    blasts = response.json()['blasts']
    assert len(blasts) == 1
    blast_id = blasts[0]['id']
    # get campaign sends
    response = send_request('get', PushCampaignApiUrl.BLAST_SENDS
                            % (campaign_in_db['id'], blast_id), token_first)
    assert response.status_code == OK
    sends = response.json()['sends']
    # get if of record of sms_campaign_send_url_conversion for this campaign
    assert len(sends) == 1
    campaign_send = sends[0]
    response = send_request('get', PushCampaignApiUrl.URL_CONVERSION_BY_SEND_ID % campaign_send['id'], token_first)
    assert response.status_code == OK
    url_conversion_obj = response.json()['url_conversion']

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.URL_CONVERSION % url_conversion['id'],
                                token_first)
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return url_conversion_obj


@pytest.fixture(scope='function')
def talent_pool(request, token_first):
    """
    This fixture created a talent pool that is associated to user_first
    :param request: request object
    :param token_first: authentication token for user_first
    """
    data = {
        "talent_pools": [
            {
                "name": randomword(20),
                "description": fake.paragraph()
            }
        ]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOLS, token_first, data=data)
    assert response.status_code == OK
    talent_pool_id = response.json()['talent_pools'][0]

    response = send_request('get', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_first)
    assert response.status_code == OK
    talent_pool = response.json()['talent_pool']
    data = {
        "talent_pools": [talent_pool_id]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOL_GROUP % 1, token_first, data=data)
    assert response.status_code == OK

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_first)
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return talent_pool


@pytest.fixture(scope='function')
def talent_pool_second(request, token_second):
    """
    This fixture created a talent pool that is associated to user_second of domain_second
    :param token_second: authentication token for user_second
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
    assert response.status_code == OK
    talent_pool = response.json()['talent_pool']
    data = {
        "talent_pools": [talent_pool_id]
    }
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOL_GROUP % 2, token_second, data=data)
    assert response.status_code == OK

    def tear_down():
        response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token_second)
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return talent_pool


@pytest.fixture(scope='function')
def candidate_first(request, talent_pool, token_first):
    """
    This fixture created a test candidate in domain first and it will be deleted
    after test has run.
    :param request: request object
    :param talent_pool: talent pool dict object associated to user_first
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
        assert response.status_code in [OK, NOT_FOUND]

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def candidate_same_domain(request, talent_pool, token_same_domain):
    """
    This fixture created a candidate in domain first  and it will be deleted
    after test has run.
    :param request: request object
    :param talent_pool: talent pool dict object
    :param token_same_domain: authentication token
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
    This fixture created a test candidate using for domain second and it will be deleted
    after test has run.
    :param request: request object
    :param token_second: authentication token for user_second
    :param talent_pool_second: talent pool dict object from domain second
    """
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
def candidate_device_first(token_first, candidate_first):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    :param token_first: authentication token
    :param candidate_first: candidate dict object
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
def candidate_device_same_domain(token_same_domain, candidate_same_domain):
    """
    This fixture associates a device with  candidate from domain first which is required to
    send push campaign to candidate.
    :param token_same_domain: authentication token
    :param candidate_same_domain: candidate dict object
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
def candidate_device_second(token_second, candidate_second):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    :param token_second: authentication token
    :param candidate_second: candidate dict object
    """
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    """
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_second['id'],
                            token_second,
                            data=data)
    response.status_code == 201
    response = send_request('get', CandidateApiUrl.DEVICES % candidate_second['id'],
                            token_second)
    assert response.status_code == OK
    devices = response.json()['devices']
    assert len(devices) == 1
    return devices[0]
