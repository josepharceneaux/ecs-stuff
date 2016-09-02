from datetime import datetime, timedelta
from dateutil.parser import parse
from faker import Faker
from contracts import contract
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi, CandidateApiUrl
from push_campaign_service.common.utils.datetime_utils import DatetimeUtils
from push_campaign_service.common.utils.api_utils import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from push_campaign_service.common.utils.handy_functions import (send_request)
from push_campaign_service.push_campaign_app import logger

fake = Faker()

API_URL = PushCampaignApiUrl.HOST_NAME
VERSION = PushCampaignApi.VERSION


def generate_campaign_data():
    """
    Generates random campaign data
    :rtype dict
    """
    data = {
        "name": fake.domain_name(),
        "body_text": fake.paragraph(1),
        "url": 'https://www.google.com/'
    }
    return data


@contract
def generate_campaign_schedule_data(frequency_id=1):
    """
    This method generates data (dict) for scheduling a campaign.
    This data contains start_date, end_datetime and frequency id
    :type frequency_id: type(t)
    :return: data
    :rtype dict
    """
    start = datetime.utcnow() + timedelta(seconds=20)
    end = datetime.utcnow() + timedelta(days=10)
    data = {
        "frequency_id": frequency_id,
        "start_datetime": DatetimeUtils.to_utc_str(start),
        "end_datetime": DatetimeUtils.to_utc_str(end)
    }
    return data


@contract
def compare_campaign_data(campaign_first, campaign_second):
    """
    This function compares two push campaign dictionaries
    It raises assertion error if respective keys' values do not match.
    :type campaign_first: dict
    :type campaign_second: dict
    """
    assert campaign_first['body_text'] == campaign_second['body_text']
    assert campaign_first['name'] == campaign_second['name']
    assert campaign_first['url'] == campaign_second['url']


@contract
def match_schedule_data(schedule_data, campaign):
    """
    This function takes schedule data and campaign object and matched schedule values like start_datetine,
    end_datetime and frequency_id.
    :param dict schedule_data: data used to schedule a campaign
    :param dict campaign: campaign object
    """
    diff = timedelta(seconds=1)
    assert (parse(schedule_data['start_datetime'].split('.')[0]) - parse(campaign['start_datetime'])) < diff
    assert (parse(schedule_data['end_datetime'].split('.')[0]) - parse(campaign['end_datetime'])) < diff
    assert schedule_data['frequency_id'] == campaign['frequency_id']


@contract
def get_campaigns(token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,)):
    """
    Get campaign of a specific user.
    Default page number is 1 and per_page (page size) is 10
    :type page: int | long
    :type per_page: int | long
    :type token: string
    :type expected_status: tuple[int]
    """
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.CAMPAIGNS + query, token)
    logger.info('tests : get_campaigns: %s', response.content)
    print('tests : get_campaigns: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def get_campaign(campaign_id, token, expected_status=(200,)):
    """
    Get a push campaign from API given by campaign id.
    :type campaign_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_id, token)
    logger.info('tests : get_campaign: %s', response.content)
    print('tests : get_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def create_campaign(data, token, expected_status=(201,)):
    """
    Send a POST request to Push Campaign API with campaign data to create a new Push Campaign.
    :type data: dict
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
    logger.info('tests : create_campaign: %s', response.content)
    print('tests : create_campaign: %s', response.content)
    assert response.status_code in expected_status
    headers = response.headers
    response = response.json()
    response['headers'] = headers
    return response


@contract
def update_campaign(campaign_id, data, token, expected_status=(200, 204)):
    """
    This method send a PUT request to Push Campaign API to updates a push campaign with given data.
    :type campaign_id: int | long
    :type data: dict
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_id, token, data)
    logger.info('tests : update_campaign: %s', response.content)
    print('tests : update_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def delete_campaign(campaign_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to Push Campaign API to delete a campaign given by campaign_id.
    :type campaign_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % campaign_id, token)
    logger.info('tests : delete_campaign: %s', response.content)
    print('tests : delete_campaign: %s', response.content)

    assert response.status_code in expected_status
    return response.json()


@contract
def delete_campaigns(data, token, expected_status=(200,)):
    """
    This method sends a DELETE request to Push Campaign API to delete multiple campaigns.
    :type data: dict
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', PushCampaignApiUrl.CAMPAIGNS, token, data=data)
    logger.info('tests : delete_campaigns: %s', response.content)
    print('tests : delete_campaigns: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def send_campaign(campaign_id, token, expected_status=(200,)):
    """
    This method sends a POST request to Push Campaign API to send a campaign to associated candidates.
    :type campaign_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    url = PushCampaignApiUrl.SEND % campaign_id
    response = send_request('post', url, token)
    logger.info('tests : send_campaign: %s', response.content)
    print('tests : send_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def get_blasts(campaign_id, token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,), count=None):
    """
    This method sends a GET request to Push Campaign API to get a list of blasts associated with
     a campaign given by campaign_id.
    :type campaign_id: int | long
    :type token: string
    :type page: int | long
    :type per_page: int | long
    :type expected_status: tuple[int]
    :type count: int | None
    :rtype dict
    """
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_id + query, token)
    logger.info('tests : get_blasts: %s', response.content)
    print('tests : get_blasts: %s', response.content)
    assert response.status_code in expected_status
    response = response.json()
    if count:
        assert len(response['blasts']) == count
    return response


@contract
def get_blast(blast_id, campaign_id, token, expected_status=(200,), sends=None):
    """
    This method sends a GET request to Push Campaign API to get a specific blast associated with
     a campaign given by campaign_id.
    :type blast_id: int | long
    :type campaign_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :type sends: int | None
    :rtype dict
    """
    response = send_request('get', PushCampaignApiUrl.BLAST % (campaign_id, blast_id),
                            token)

    assert response.status_code in expected_status
    response = response.json()
    if sends:
        assert response['blast']['sends'] == sends
    return response


@contract
def get_blast_sends(blast_id, campaign_id, token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE,
                    expected_status=(200,), count=None):
    """
    This method sends a GET request to Push Campaign API to get a list of sends associated to a specific blast.
    :type blast_id: int | long
    :type campaign_id: int | long
    :type token: string
    :type page: int | long
    :type per_page: int | long
    :type expected_status: tuple[int]
    :type count: int | None
    :rtype dict
    """
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.BLAST_SENDS % (campaign_id, blast_id) + query,
                            token)
    assert response.status_code in expected_status
    response = response.json()
    if count:
        assert len(response['sends']) == count
    return response


@contract
def get_campaign_sends(campaign_id, token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,),
                       count=None):
    """
    This method sends a GET request to Push Campaign API to get a list of sends associated with
     a campaign.
    :type campaign_id: int | long
    :type token: string
    :type page: int | long
    :type per_page: int | long
    :type expected_status: tuple[int]
    :type count: int | None
    :rtype dict
    """
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.SENDS % campaign_id + query, token)
    logger.info('tests: get_campaign_sends: %s', response.content)
    print('tests: get_campaign_sends: %s', response.content)
    assert response.status_code in expected_status
    response = response.json()
    if count:
        assert len(response['sends']) == count
    return response


@contract
def schedule_campaign(campaign_id, data, token, expected_status=(200,)):
    """
    This method sends a POST request to Push Campaign API to schedule a push campaign with given schedule data.
    :type campaign_id: int | long
    :type data: dict
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    logger.info('tests : schedule_campaign: Going to schedule push campaign (id: %s)' % campaign_id)
    response = send_request('post', PushCampaignApiUrl.SCHEDULE % campaign_id, token, data)
    logger.info('tests : schedule_campaign: %s', response.content)
    print('tests : schedule_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def reschedule_campaign(campaign_id, data, token, expected_status=(200,)):
    """
    This method sends a PUT request to Push Campaign API to reschedule a push campaign with given schedule data.
    :type campaign_id: int | long
    :type data: dict
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('put', PushCampaignApiUrl.SCHEDULE % campaign_id, token, data)
    logger.info('tests: reschedule_campaign: %s', response.content)
    print('tests: reschedule_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


@contract
def unschedule_campaign(campaign_id, token, expected_status=(200,)):
    """
    This method sends a DELETE request to Push Campaign API to unschedule a push campaign.
    :type campaign_id: int | long
    :type token: string
    :type expected_status: tuple[int]
    :rtype dict
    """
    response = send_request('delete', PushCampaignApiUrl.SCHEDULE % campaign_id, token)
    logger.info('tests : unschedule_campaign: %s', response.content)
    print('tests : unschedule_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()
