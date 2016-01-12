import json
from datetime import datetime, timedelta
import requests
from faker import Faker
from push_campaign_service.common.routes import  PushCampaignApiUrl
from push_campaign_service.common.utils.handy_functions import to_utc_str

fake = Faker()


def send_request(method, url, access_token, data=None, is_json=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


def unauthorize_test(method, url, access_token, data=None):
    # TODO: Use a hard coded token invalid
    response = send_request(method, url, access_token,  data)
    assert response.status_code == 401


def missing_key_test(data, key, token):
    del data[key]
    response = send_request('post', PushCampaignApiUrl.CAMPAIGNS, token, data)
    assert response.status_code == 500
    response = response.json()
    error = response['error']
    assert error['code'] == 7003
    assert error['message'] == 'Some required fields are missing'
    assert error['missing_fields'] == [key]


def invalid_value_test(data, key, token, campaign_id):
    data.update(**generate_campaign_data())
    data[key] = ''
    response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_id, token, data)
    response.status_code == 400, 'InvalidUsage exception raised'
    response = response.json()
    error = response['error']
    assert error['message'] == 'Invalid value for field in campaign data'
    assert error['field'] == key
    assert error['invalid_value'] == data[key]


def invalid_data_test(method, url, token):
    data = None
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == 400
    error = response.json()['error']
    assert error['message'] == 'Kindly send request with JSON data and application/json content-type header'
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == 400
    error = response.json()['error']
    assert error['message'] == 'Kindly send request with JSON data and application/json content-type header'
    data = {}
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == 400
    error = response.json()['error']
    assert error['message'] == 'Request data is empty'
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == 400
    error = response.json()['error']
    assert error['message'] == 'Kindly send request with JSON data and application/json content-type header'
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == 400
    error = response.json()['error']
    assert error['message'] == 'Kindly send request with JSON data and application/json content-type header'


def generate_campaign_data():
    """ Get random campaign data
    """
    data = {
        "name": fake.domain_name(),
        "body_text": fake.paragraph(1),
        "url": fake.url()
    }
    return data


def generate_campaign_schedule_data():
    """
    This method generates data (dict) for scheduling a campaign.
    This data contains start_date, end_datetime and frequency id
    :return:
    """
    start = datetime.utcnow() + timedelta(seconds=10)
    end = datetime.utcnow() + timedelta(days=10)
    data = {
        "frequency_id": 2,
        "start_datetime": to_utc_str(start),
        "end_datetime": to_utc_str(end)
    }
    return data


def get_fake_dict():
    """
    This method just creates a dictionary with 3 random keys and values

    : Example:

        data = {
                    'excepturi': 'qui',
                    'unde': 'ipsam',
                    'magni': 'voluptate'
                }
    :return: data
    :rtype dict
    """
    data = dict()
    for _ in range(3):
        data[fake.word()] = fake.word()
    return data


def compare_campaign_data(campaign_obj, campaign_dict):
    _id = campaign_obj['id'] if isinstance(campaign_obj, dict) else campaign_obj.id
    body_text = campaign_obj['body_text'] if isinstance(campaign_obj, dict) else campaign_obj.body_text
    name = campaign_obj['name'] if isinstance(campaign_obj, dict) else campaign_obj.name
    url = campaign_obj['url'] if isinstance(campaign_obj, dict) else campaign_obj.url
    assert _id == campaign_dict['id']
    assert body_text == campaign_dict['body_text']
    assert name == campaign_dict['name']
    assert url == campaign_dict['url']
