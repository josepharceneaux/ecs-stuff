from datetime import datetime, timedelta
from faker import Faker
from requests import codes as HttpStatus
from push_campaign_service.common.campaign_services.custom_errors import CampaignException
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi, CandidateApiUrl
from push_campaign_service.common.utils.handy_functions import to_utc_str
from push_campaign_service.common.utils.api_utils import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from push_campaign_service.common.utils.test_utils import (send_request,
                                                           get_fake_dict)
from push_campaign_service.push_campaign_app import logger

fake = Faker()

API_URL = PushCampaignApiUrl.HOST_NAME
VERSION = PushCampaignApi.VERSION
SLEEP_TIME = 20


def missing_key_test(data, key, token):
    """
    This function sends a put request to api with data with one required field
    missing and checks that it InvalidUsage 400
    :param data: campaign data
    :type data dict
    :param key: field key
    :type key: str
    :param token: auth token
    :rtype token: str
    :param campaign_id: push campaign id
    :type campaign_id: int | long
    """
    del data[key]
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
    assert response.status_code == HttpStatus.BAD_REQUEST
    response = response.json()
    error = response['error']
    assert error['code'] == CampaignException.MISSING_REQUIRED_FIELD
    assert error['missing_fields'] == [key]


def invalid_value_test(data, key, token, campaign_id):
    """
    This function sends a put request to api with required one required field
    with an invalid value (empty string) and checks that it returns InvalidUsage 400
    :param data: campaign data
    :type data dict
    :param key: field key
    :type key: str
    :param token: auth token
    :rtype token: str
    :param campaign_id: push campaign id
    :type campaign_id: int | long
    """
    data.update(**generate_campaign_data())
    data[key] = ''
    response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_id, token, data)
    response.status_code == HttpStatus.BAD_REQUEST
    response = response.json()
    error = response['error']
    assert error['field'] == key
    assert error['invalid_value'] == data[key]


def invalid_data_test(method, url, token):
    """
    This functions sends http request to a given url with different
    invalid data and checks for InvalidUsage
    :param method: http method e.g. POST, PUT
    :param url: api url
    :param token: auth token
    """
    data = None
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == HttpStatus.BAD_REQUEST
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == HttpStatus.BAD_REQUEST
    data = {}
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == HttpStatus.BAD_REQUEST
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == HttpStatus.BAD_REQUEST
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == HttpStatus.BAD_REQUEST


def generate_campaign_data():
    """ Generates random campaign data
    :return data
    :rtype dict
    """
    data = {
        "name": fake.domain_name(),
        "body_text": fake.paragraph(1),
        "url": 'https://www.google.com/'
    }
    return data


def generate_campaign_schedule_data():
    """
    This method generates data (dict) for scheduling a campaign.
    This data contains start_date, end_datetime and frequency id
    :return: data
    :rtype dict
    """
    start = datetime.utcnow() + timedelta(seconds=20)
    end = datetime.utcnow() + timedelta(days=10)
    data = {
        "frequency_id": 2,
        "start_datetime": to_utc_str(start),
        "end_datetime": to_utc_str(end)
    }
    return data


def compare_campaign_data(campaign_first, campaign_second):
    """
    This function compares two push campaign dictionaries
    It raises assertion error if respective keys' values do not match.
    """
    assert campaign_first['body_text'] == campaign_second['body_text']
    assert campaign_first['name'] == campaign_second['name']
    assert campaign_first['url'] == campaign_second['url']


def get_campaigns(token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,)):
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.CAMPAIGNS + query, token)
    logger.info('tests : get_campaigns: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def get_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_id, token)
    logger.info('tests : get_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def create_campaign(data, token, expected_status=(201,)):
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
    logger.info('tests : create_campaign: %s', response.content)
    assert response.status_code in expected_status
    headers = response.headers
    response = response.json()
    response['headers'] = headers
    return response


def update_campaign(campaign_id, data, token, expected_status=(200, 204)):
    response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_id, token, data)
    logger.info('tests : update_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % campaign_id, token)
    logger.info('tests : delete_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_campaigns(data, token, expected_status=(200,)):
    response = send_request('delete', PushCampaignApiUrl.CAMPAIGNS, token, data=data)
    logger.info('tests : delete_campaigns: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def send_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('post', PushCampaignApiUrl.SEND % campaign_id, token)
    logger.info('tests : send_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def get_blasts(campaign_id, token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,)):
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_id + query, token)
    logger.info('tests : get_blasts: %s', response.content)
    print(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_blast(blast_id, campaign_id, token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.BLAST % (campaign_id, blast_id),
                            token)

    assert response.status_code in expected_status
    return response.json()


def get_blast_sends(blast_id, campaign_id, token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,)):
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.BLAST_SENDS % (campaign_id, blast_id) + query,
                            token)
    assert response.status_code in expected_status
    return response.json()


def get_campaign_sends(campaign_id, token, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE, expected_status=(200,)):
    query = '?page=%s&per_page=%s' % (page, per_page)
    response = send_request('get', PushCampaignApiUrl.SENDS % campaign_id + query, token)
    assert response.status_code in expected_status
    return response.json()


def schedule_campaign(campaign_id, data, token, expected_status=(200,)):
    logger.info('tests : schedule_campaign: Going to schedule push campaign (id: %s)' % campaign_id)
    response = send_request('post', PushCampaignApiUrl.SCHEDULE % campaign_id, token, data)
    logger.info('tests : schedule_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def reschedule_campaign(campaign_id, data, token, expected_status=(200,)):
    response = send_request('put', PushCampaignApiUrl.SCHEDULE % campaign_id, token, data)
    logger.info('tests: reschedule_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def unschedule_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('delete', PushCampaignApiUrl.SCHEDULE % campaign_id, token)
    logger.info('tests : unschedule_campaign: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def associate_device_to_candidate(candidate_id, device_id, token, expected_status=(201,)):
    data = {
        'one_signal_device_id': device_id
    }
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_id, token, data=data)
    logger.info('tests : associate_device_to_candidate: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def get_candidate_devices(candidate_id, token, expected_status=(200,)):
    response = send_request('get', CandidateApiUrl.DEVICES % candidate_id, token)
    logger.info('tests : get_candidate_devices: %s', response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_candidate_device(candidate_id, device_id,  token, expected_status=(200,)):
    data = {
        'one_signal_device_id': device_id
    }
    response = send_request('delete', CandidateApiUrl.DEVICES % candidate_id, token, data=data)
    logger.info('tests : delete_candidate_devices: %s', response.content)
    assert response.status_code in expected_status
    return response.json()
