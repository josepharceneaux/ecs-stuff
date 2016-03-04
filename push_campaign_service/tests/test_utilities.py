from datetime import datetime, timedelta
from faker import Faker

from push_campaign_service.common.campaign_services.custom_errors import CampaignException
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi, \
    CandidatePoolApiUrl, SchedulerApiUrl, CandidateApiUrl
from push_campaign_service.common.tests.conftest import randomword
from push_campaign_service.common.utils.handy_functions import to_utc_str
from push_campaign_service.common.utils.test_utils import (send_request,
                                                           get_fake_dict, HttpStatus)
from push_campaign_service.modules.constants import PUSH_DEVICE_ID
from push_campaign_service.push_campaign_app import logger

fake = Faker()

API_URL = PushCampaignApiUrl.HOST_NAME
VERSION = PushCampaignApi.VERSION
SLEEP_TIME = 20

# TODO: name of the file tells me that here will be tests for utility methods. But here
# TODO: we have helper methods. IMO, these should be in (e.g) tests/modules/handy_functions.py


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
    :return:
    """
    del data[key]
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
    assert response.status_code == HttpStatus.INVALID_USAGE
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
    :return:
    """
    data.update(**generate_campaign_data())
    data[key] = ''
    response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_id, token, data)
    response.status_code == HttpStatus.INVALID_USAGE
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
    :return:
    """
    data = None
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == HttpStatus.INVALID_USAGE
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == HttpStatus.INVALID_USAGE
    data = {}
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == HttpStatus.INVALID_USAGE
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == HttpStatus.INVALID_USAGE
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == HttpStatus.INVALID_USAGE


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
    :return:
    """
    assert campaign_first['body_text'] == campaign_second['body_text']
    assert campaign_first['name'] == campaign_second['name']
    assert campaign_first['url'] == campaign_second['url']


def get_campaigns(token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.CAMPAIGNS, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def create_campaign(data, token, expected_status=(201,)):
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
    logger.info(response.content)
    assert response.status_code in expected_status
    headers = response.headers
    response = response.json()
    response['headers'] = headers
    return response


def update_campaign(campaign_id, data, token, expected_status=(200, 204)):
    response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_id, token, data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % campaign_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_campaigns(data, token, expected_status=(200,)):
    response = send_request('delete', PushCampaignApiUrl.CAMPAIGNS, token, data=data)
    assert response.status_code in expected_status
    return response.json()


def send_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('post', PushCampaignApiUrl.SEND % campaign_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_blasts(campaign_id, token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_blast(blast_id, campaign_id, token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.BLAST % (campaign_id, blast_id),
                            token)
    assert response.status_code in expected_status
    return response.json()


def get_blast_sends(blast_id, campaign_id, token,  expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.BLAST_SENDS % (campaign_id, blast_id),
                            token)
    assert response.status_code in expected_status
    return response.json()


def get_campaign_sends(campaign_id, token, expected_status=(200,)):
    response = send_request('get', PushCampaignApiUrl.SENDS % campaign_id, token)
    assert response.status_code in expected_status
    return response.json()


def create_smartlist(candidate_ids, token, expected_status=(201,)):
    assert isinstance(candidate_ids, (list, tuple)), 'candidate_ids must be list or tuple'
    data = {
        'candidate_ids': candidate_ids,
        'name': fake.word()
    }
    response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, token, data=data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_smartlist(smartlist_id, token, expected_status=(200,)):
    response = send_request('delete', CandidatePoolApiUrl.SMARTLIST % smartlist_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def create_talent_pools(token, count=1, expected_status=(200,)):
    data = {
        "talent_pools": []
    }
    for index in xrange(count):
        talent_pool = {
                "name": randomword(20),
                "description": fake.paragraph()
            }
        data["talent_pools"].append(talent_pool)
    response = send_request('post', CandidatePoolApiUrl.TALENT_POOLS, token, data=data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_talent_pool(talent_pool_id, token, expected_status=(200,)):
    response = send_request('get', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def schedule_campaign(campaign_id, data, token, expected_status=(200,)):
    response = send_request('post', PushCampaignApiUrl.SCHEDULE % campaign_id, token, data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def reschedule_campaign(campaign_id, data, token, expected_status=(200,)):
    response = send_request('put', PushCampaignApiUrl.SCHEDULE % campaign_id, token, data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def unschedule_campaign(campaign_id, token, expected_status=(200,)):
    response = send_request('delete', PushCampaignApiUrl.SCHEDULE % campaign_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_scheduler_task(task_id, token, expected_status=(200,)):
    response = send_request('delete', SchedulerApiUrl.TASK % task_id, token)
    assert response.status_code in expected_status
    return response.json()


def delete_talent_pool(talent_pool_id, token, expected_status=(200,)):
    response = send_request('delete', CandidatePoolApiUrl.TALENT_POOL % talent_pool_id,
                            token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def create_candidate(talent_pool_id, token, expected_status=(201,)):
    data = {
        "candidates": [
            {
                "first_name": fake.first_name(),
                "middle_name": fake.user_name(),
                "last_name": fake.last_name(),
                "talent_pool_ids": {
                    "add": [talent_pool_id]
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
    response = send_request('post', CandidateApiUrl.CANDIDATES, token, data=data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_candidate(candidate_id, token, expected_status=(200,)):
    response = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def delete_candidate(candidate_id, token, expected_status=(200,)):
    response = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status


def associate_device_to_candidate(candidate_id, token, expected_status=(201,)):
    data = {
        'one_signal_device_id': PUSH_DEVICE_ID
    }
    response = send_request('post', CandidateApiUrl.DEVICES % candidate_id, token, data=data)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()


def get_candidate_devices(candidate_id, token, expected_status=(200,)):
    response = send_request('get', CandidateApiUrl.DEVICES % candidate_id, token)
    logger.info(response.content)
    assert response.status_code in expected_status
    return response.json()
