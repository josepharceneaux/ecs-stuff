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
from redo import retry
from requests import codes

from push_campaign_service.common.models.misc import Frequency
from push_campaign_service.common.utils.test_utils import (delete_scheduler_task,
                                                           create_smartlist, get_smartlist_candidates, delete_smartlist)
from push_campaign_service.common.test_config_manager import load_test_config
from push_campaign_service.common.tests.api_conftest import (token_first, token_same_domain,
                                                             token_second, user_first,
                                                             user_same_domain, user_second,
                                                             candidate_first, candidate_same_domain,
                                                             candidate_second, smartlist_first,
                                                             smartlist_same_domain, smartlist_second,
                                                             talent_pool, talent_pool_second, talent_pipeline,
                                                             talent_pipeline_second)
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.tests.test_utilities import (generate_campaign_data, send_request,
                                                        generate_campaign_schedule_data,
                                                        get_campaigns, create_campaign,
                                                        delete_campaign, send_campaign,
                                                        get_blasts, schedule_campaign,
                                                        associate_device_to_candidate,
                                                        delete_campaigns, delete_candidate_device, get_campaign_sends)

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
            assert response.status_code in [codes.OK, codes.NOT_FOUND]
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
    :return: campaign dict object
    """
    previous_count = len(get_campaigns(token_first)['campaigns'])
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_first['id']]
    campaign_id = create_campaign(data, token_first)['id']
    data['id'] = campaign_id
    data['previous_count'] = previous_count

    def tear_down():
        delete_campaign(campaign_id, token_first, expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_in_db_multiple_smartlists(request, token_first, smartlist_first, campaign_data,
                                       smartlist_same_domain, candidate_device_first, candidate_device_same_domain):
    """
    This fixtures creates a campaign which is associated with multiple (two) smartlists.
    :param request:
    :param token_first: at belongs to same users, and one created by other
    user from same domain
    :param smartlist_first: smartlist dict object owned by user_first
    :param smartlist_same_domain: smartlist dict object owned by user_same_domain
    :param campaign_data: dict data to create campaign
    :return: campaign data
    """
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_first['id'], smartlist_same_domain['id']]
    campaign_id = create_campaign(data, token_first)['id']
    data['id'] = campaign_id

    def tear_down():
        delete_campaign(campaign_id, token_first, expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_with_two_candidates_with_and_without_push_device(request, token_first, campaign_data,
                                                smartlist_with_two_candidates_with_and_without_device_associated):
    """
    This fixtures creates a campaign which is associated with one smartlist having two candidates.
    One candidate has a push device but other does not.
    :param request:
    :param token_first: auth token for user_first
    :param smartlist_with_two_candidates_with_and_without_device_associated: smartlist dict object owned by user_first
    :param campaign_data: dict data to create campaign
    :return: campaign data
    """
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_with_two_candidates_with_and_without_device_associated['id']]
    campaign_id = create_campaign(data, token_first)['id']
    data['id'] = campaign_id

    def tear_down():
        delete_campaign(campaign_id, token_first, expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_with_two_candidates_with_no_push_device_associated(request, token_first,
                                                                smartlist_with_two_candidates_with_no_device_associated,
                                                                campaign_data):
    """
    This fixtures creates a campaign which is associated with one smartlist having two candidates. One candidate
    has a push device but other does not.
    :param request:
    :param token_first: at belongs to same users, and one created by other
    user from same domain
    :param smartlist_with_two_candidates_with_no_device_associated: smartlist dict object owned by user_first
    :param campaign_data: dict data to create campaign
    :return: campaign data
    """
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_with_two_candidates_with_no_device_associated['id']]
    campaign_id = create_campaign(data, token_first)['id']
    data['id'] = campaign_id

    def tear_down():
        delete_campaign(campaign_id, token_first, expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_in_db_same_domain(request, token_same_domain, smartlist_same_domain, campaign_data):
    """
    This fixture creates a campaign in database by hitting push campaign service api
    :param request: request object
    :param token_same_domain: authentication token for user_first
    :param smartlist_same_domain: smartlist dict object
    :param campaign_data: data to create campaign
    :return: campaign dict object
    """
    previous_count = len(get_campaigns(token_same_domain)['campaigns'])
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_same_domain['id']]
    campaign_id = create_campaign(data, token_same_domain)['id']
    data['id'] = campaign_id
    data['previous_count'] = previous_count

    def tear_down():
        delete_campaign(campaign_id, token_same_domain, expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaign_in_db_second(request, token_second, user_second, smartlist_second, campaign_data):
    """
    This fixture creates a push campaign in database for sample_user
    user_second fixture is required here to add ROLLS for user.
    :param request:
    :param token_second: token for user_second
    :param smartlist_second: test smartlist associated to user_second
    :param campaign_data: dictionary containing campaign data
    :return: campaign data
    """
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_second['id']]
    campaign_id = create_campaign(data, token_second)['id']
    data['id'] = campaign_id

    def tear_down():
        delete_campaign(campaign_id, token_second, expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return data


@pytest.fixture()
def campaigns_for_pagination_test(request, token_first, smartlist_first, campaign_data):
    """
    This fixture creates a multiple campaigns to test pagination functionality.
    :param request: request object
    :param token_first: authentication token for user_first
    :param smartlist_first: smartlist dict object
    :param campaign_data: data to create campaign
    :return: campaigns count
    """
    campaigns_count = 15
    data = campaign_data.copy()
    data['smartlist_ids'] = [smartlist_first['id']]
    ids = []
    for _ in xrange(campaigns_count):
        id_ = create_campaign(data, token_first)['id']
        ids.append(id_)

    def tear_down():
        data = {
            'ids': ids
        }
        delete_campaigns(data, token_first, expected_status=(codes.OK, codes.MULTI_STATUS))

    request.addfinalizer(tear_down)
    return campaigns_count


@pytest.fixture()
def campaign_blast(token_first, campaign_in_db, smartlist_first, candidate_device_first):
    """
    This fixture creates a campaign blast for given campaign by sending a campaign
    :param token_first: authentication token
    :param campaign_in_db: campaign dict object
    :param candidate_device_first: candidate device dict object
    :return: campaign's blast dict object
    """
    send_campaign(campaign_in_db['id'], token_first)
    response = get_blasts(campaign_in_db['id'], token_first)
    blasts = response['blasts']
    assert len(blasts) == 1
    blast = blasts[0]
    blast['campaign_id'] = campaign_in_db['id']
    return blast


@pytest.fixture()
def campaign_blasts(campaign_in_db, token_first, smartlist_first, candidate_device_first):
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
    blasts = get_blasts(campaign_in_db['id'], token_first)['blasts']
    return blasts


@pytest.fixture()
def campaign_blasts_pagination(campaign_in_db, token_first, smartlist_first, candidate_device_first):
    """
    This fixture hits Push campaign api to send campaign which in turn creates blast.
    But this time we will create 15 blasts to test pagination results
    At the end just return blasts count.
    :param candidate_device_first: device associated to first candidate
    :param campaign_in_db: push campaign object
    :param token_first: auth token
    """
    blasts_counts = 15
    for num in range(blasts_counts):
        send_campaign(campaign_in_db['id'], token_first)
    return blasts_counts


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
    data = generate_campaign_schedule_data(frequency_id=Frequency.DAILY)
    task_id = schedule_campaign(campaign_in_db['id'], data, token_first)['task_id']

    def fin():
        delete_scheduler_task(task_id, token_first,
                              expected_status=(codes.OK, codes.NOT_FOUND))

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
    :return: url_conversion dict object
    """
    response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db['id'], token_first)
    assert response.status_code == codes.OK
    # get campaign sends
    response = retry(get_campaign_sends, sleeptime=3, attempts=10, retry_exceptions=(AssertionError,),
                     args=(campaign_in_db['id'], token_first), kwargs={'count': 1})
    sends = response['sends']
    campaign_send = sends[0]
    response = send_request('get', PushCampaignApiUrl.URL_CONVERSION_BY_SEND_ID % campaign_send['id'], token_first)
    assert response.status_code == codes.OK
    url_conversion_obj = response.json()['url_conversion']

    def tear_down():
        response = send_request('delete', PushCampaignApiUrl.URL_CONVERSION % url_conversion_obj['id'],
                                token_first)
        assert response.status_code in [codes.OK, codes.NOT_FOUND, codes.FORBIDDEN]

    request.addfinalizer(tear_down)
    return url_conversion_obj


@pytest.fixture(scope='function')
def candidate_device_first(request, token_first, candidate_first):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    :param token_first: authentication token
    :param candidate_first: candidate dict object
    """
    candidate_id = candidate_first['id']
    device_id = test_config['PUSH_CONFIG']['device_id_1']
    device = {'id':  associate_device_to_candidate(candidate_id, device_id, token_first),
              'one_signal_id': device_id}

    def tear_down():
        delete_candidate_device(candidate_id, device_id, token_first, expected_status=(codes.OK,
                                                                                       codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return device


@pytest.fixture(scope='function')
def candidate_device_same_domain(request, token_same_domain, candidate_same_domain):
    """
    This fixture associates a device with  candidate from domain first which is required to
    send push campaign to candidate.
    :param token_same_domain: authentication token
    :param candidate_same_domain: candidate dict object
    """
    candidate_id = candidate_same_domain['id']
    device_id = test_config['PUSH_CONFIG']['device_id_1']
    device = {'id':  associate_device_to_candidate(candidate_id, device_id, token_same_domain),
              'one_signal_id': device_id}

    def tear_down():
        delete_candidate_device(candidate_id, device_id, token_same_domain,
                                expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return device


@pytest.fixture(scope='function')
def candidate_device_second(request, token_second, candidate_second):
    """
    This fixture associates a device with test candidate which is required to
    send push campaign to candidate.
    :param token_second: authentication token
    :param candidate_second: candidate dict object
    """
    candidate_id = candidate_second['id']
    device_id = test_config['PUSH_CONFIG']['device_id_1']
    device = {'id':  associate_device_to_candidate(candidate_id, device_id, token_second),
              'one_signal_id': device_id}

    def tear_down():
        delete_candidate_device(candidate_id, device_id, token_second, expected_status=(codes.OK,
                                                                                        codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return device


@pytest.fixture(scope='function')
def smartlist_with_two_candidates_with_and_without_device_associated(request, token_first, user_first, candidate_first,
                                                                     candidate_same_domain, talent_pipeline,
                                                                     candidate_device_first):
    """
    This fixture creates a smartlist that contains two candidates from domain_first. One candidate has a
    push device associated with him, but other candidate does not have any push device associated.
    :param request: request object
    :param candidate_first: candidate object
    :param candidate_same_domain: candidate object
    :param token_first: access token for user_first
    :return: smartlist object (dict)
    """
    candidate_ids = [candidate_first['id'], candidate_same_domain['id']]
    time.sleep(10)
    smartlist = create_smartlist(candidate_ids, talent_pipeline['id'], token_first)['smartlist']
    smartlist_id = smartlist['id']
    retry(get_smartlist_candidates, sleeptime=3, attempts=50, sleepscale=1, retry_exceptions=(AssertionError,),
          args=(smartlist_id, token_first), kwargs={'count': 2})

    def tear_down():
        delete_smartlist(smartlist_id, token_first,
                         expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_with_two_candidates_with_no_device_associated(request, token_first, user_first, candidate_first,
                                                            candidate_same_domain, talent_pipeline):
    """
    This fixture creates a smartlist that contains two candidates from domain_first.
    Both candidates do not have any push device associated with them.
    :param request: request object
    :param candidate_first: candidate object
    :param candidate_same_domain: candidate object
    :param token_first: access token for user_first
    :return: smartlist object (dict)
    """
    candidate_ids = [candidate_first['id'], candidate_same_domain['id']]
    time.sleep(10)
    smartlist = create_smartlist(candidate_ids, talent_pipeline['id'], token_first)['smartlist']
    smartlist_id = smartlist['id']
    retry(get_smartlist_candidates, sleeptime=3, attempts=50, sleepscale=1, retry_exceptions=(AssertionError,),
          args=(smartlist_id, token_first), kwargs={'count': 2})

    def tear_down():
        delete_smartlist(smartlist_id, token_first,
                         expected_status=(codes.OK, codes.NOT_FOUND))

    request.addfinalizer(tear_down)
    return smartlist
