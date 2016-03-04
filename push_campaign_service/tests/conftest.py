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

from push_campaign_service.common.utils.test_utils import HttpStatus
# TODO: IMO folloing should be removed
from push_campaign_service.push_campaign_app import logger
from push_campaign_service.common.tests.conftest import randomword
# TODO: IMO folloing should be removed
from push_campaign_service.modules.constants import PUSH_DEVICE_ID
from push_campaign_service.common.test_config_manager import load_test_config
from push_campaign_service.common.tests.api_conftest import (token_first, token_same_domain,
                                                             token_second, user_first,
                                                             user_same_domain, user_second)
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.tests.test_utilities import (generate_campaign_data, send_request,
                                                        generate_campaign_schedule_data, SLEEP_TIME,
                                                        get_campaigns,
                                                        create_campaign, delete_campaign,
                                                        send_campaign, get_blasts, create_smartlist,
                                                        delete_smartlist, schedule_campaign,
                                                        delete_scheduler_task, create_talent_pools,
                                                        get_talent_pool, delete_talent_pool,
                                                        create_candidate, get_candidate,
                                                        delete_candidate,
                                                        associate_device_to_candidate,
                                                        get_candidate_devices)


CONFIG_FILE_NAME = "test.cfg"
# TODO: How we suppose this will work everywhere? I think I gave this feedback earlier as well.
# TODO: Kindly enlighten.
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
            assert response.status_code in [HttpStatus.OK, HttpStatus.NOT_FOUND]
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
    previous_count = len(get_campaigns(token_first)['campaigns'])
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_first['id']]
    id = create_campaign(data, token_first)['id']
    data['id'] = id
    data['previous_count'] = previous_count

    def tear_down():
        delete_campaign(id, token_first, expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

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
    id = create_campaign(data, token_first)['id']
    data['id'] = id

    def tear_down():
        delete_campaign(id, token_first, expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

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
    id = create_campaign(data, token_second)['id']
    data['id'] = id

    def tear_down():
        delete_campaign(id, token_second, expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

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
    send_campaign(campaign_in_db['id'], token_first)
    time.sleep(SLEEP_TIME)
    blasts = get_blasts(campaign_in_db['id'], token_first)['blasts']
    assert len(blasts) == 1
    blast = blasts[0]
    blast['campaign_id'] = campaign_in_db['id']
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
    candidate_ids = [candidate_first['id']]
    smartlist = create_smartlist(candidate_ids, token_first)['smartlist']
    smartlist_id = smartlist['id']

    def tear_down():
        delete_smartlist(smartlist_id, token_first,
                         expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
# TODO: user_second can be removed
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
    candidate_ids = [candidate_second['id']]
    smartlist = create_smartlist(candidate_ids, token_second)['smartlist']
    smartlist_id = smartlist['id']

    def tear_down():
        delete_smartlist(smartlist_id, token_second,
                         expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))
    request.addfinalizer(tear_down)
    return smartlist



@pytest.fixture(scope='function')
# TODO: typo in name
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
    candidate_ids = [candidate_same_domain['id']]
    smartlist = create_smartlist(candidate_ids, token_same_domain)['smartlist']
    smartlist_id = smartlist['id']

    def tear_down():
        delete_smartlist(smartlist_id, token_same_domain,
                         expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

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
        send_campaign(campaign_in_db['id'], token_first)
    time.sleep(SLEEP_TIME)
    blasts = get_blasts(campaign_in_db['id'], token_first)['blasts']
    return blasts


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
    task_id = schedule_campaign(campaign_in_db['id'], data, token_first)['task_id']

    def fin():
        delete_scheduler_task(task_id, token_first,
                              expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

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
    assert response.status_code == HttpStatus.OK
    time.sleep(SLEEP_TIME)  # had to add this as sending process runs on celery
    # get campaign blast
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
    assert response.status_code == HttpStatus.OK
    blasts = response.json()['blasts']
    assert len(blasts) == 1
    blast_id = blasts[0]['id']
    # get campaign sends
    response = send_request('get', PushCampaignApiUrl.BLAST_SENDS
                            % (campaign_in_db['id'], blast_id), token_first)
    assert response.status_code == HttpStatus.OK
    sends = response.json()['sends']
    # get if of record of sms_campaign_send_url_conversion for this campaign
    assert len(sends) == 1
    campaign_send = sends[0]
    response = send_request('get', PushCampaignApiUrl.URL_CONVERSION_BY_SEND_ID % campaign_send['id'], token_first)
    assert response.status_code == HttpStatus.OK
    url_conversion_obj = response.json()['url_conversion']

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.URL_CONVERSION % url_conversion_obj['id'],
                                token_first)
        assert response.status_code in [HttpStatus.OK, HttpStatus.NOT_FOUND]

    request.addfinalizer(tear_down)
    return url_conversion_obj


@pytest.fixture(scope='function')
def talent_pool(request, token_first):
    """
    This fixture created a talent pool that is associated to user_first
    :param request: request object
    :param token_first: authentication token for user_first
    """
    talent_pools = create_talent_pools(token_first)
    talent_pool_id = talent_pools['talent_pools'][0]
    talent_pool_obj = get_talent_pool(talent_pool_id, token_first)['talent_pool']

    def tear_down():
        delete_talent_pool(talent_pool_id, token_first,
                           expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return talent_pool_obj


@pytest.fixture(scope='function')
def talent_pool_second(request, token_second):
    """
    This fixture created a talent pool that is associated to user_second of domain_second
    :param token_second: authentication token for user_second
    """
    talent_pools = create_talent_pools(token_second)
    talent_pool_id = talent_pools['talent_pools'][0]
    talent_pool_obj = get_talent_pool(talent_pool_id, token_second)['talent_pool']

    def tear_down():
        delete_talent_pool(talent_pool_id, token_second,
                           expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return talent_pool_obj


@pytest.fixture(scope='function')
# TODO: This is awesome. can we move this (and similar coftests)to common conftest?
def candidate_first(request, talent_pool, token_first):
    """
    This fixture created a test candidate in domain first and it will be deleted
    after test has run.
    :param request: request object
    :param talent_pool: talent pool dict object associated to user_first
    """
    response = create_candidate(talent_pool['id'], token_first)
    candidate_id = response['candidates'][0]['id']
    candidate = get_candidate(candidate_id, token_first)['candidate']

    def tear_down():
        delete_candidate(candidate_id, token_first,
                         expected_status=(HttpStatus.UPDATED, HttpStatus.NOT_FOUND))

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
    response = create_candidate(talent_pool['id'], token_same_domain)
    candidate_id = response['candidates'][0]['id']
    candidate = get_candidate(candidate_id, token_same_domain)['candidate']

    def tear_down():
        delete_candidate(candidate_id, token_same_domain,
                         expected_status=(HttpStatus.UPDATED, HttpStatus.NOT_FOUND))

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
    response = create_candidate(talent_pool_second['id'], token_second)
    candidate_id = response['candidates'][0]['id']
    candidate = get_candidate(candidate_id, token_second)['candidate']

    def tear_down():
        delete_candidate(candidate_id, token_second,
                         expected_status=(HttpStatus.UPDATED, HttpStatus.NOT_FOUND))

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
    candidate_id = candidate_first['id']
    associate_device_to_candidate(candidate_id, token_first)
    devices = get_candidate_devices(candidate_id, token_first)['devices']
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
    candidate_id = candidate_same_domain['id']
    associate_device_to_candidate(candidate_id, token_same_domain)
    devices = get_candidate_devices(candidate_id, token_same_domain)['devices']
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
    candidate_id = candidate_second['id']
    associate_device_to_candidate(candidate_id, token_second)
    devices = get_candidate_devices(candidate_id, token_second)['devices']
    assert len(devices) == 1
    return devices[0]
