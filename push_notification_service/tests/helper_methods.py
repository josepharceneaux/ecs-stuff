import json

import requests
from faker import Faker

from push_notification_service.common.routes import PushNotificationServiceApi


fake = Faker()

API_URL = PushNotificationServiceApi.HOST_NAME
VERSION = PushNotificationServiceApi.VERSION


def send_request(method, relative_url, access_token, data=None):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    return request_method(API_URL + relative_url, data=json.dumps(data),
                          headers={'Authorization': 'Bearer %s' % access_token,
                                   'Content-Type': 'application/json'})


def unauthorize_test(method, relative_url, access_token, data=None):
    response = send_request(method, relative_url, access_token,  data)
    assert response.status_code == 401, 'Access token is not valid'


def missing_key_test(data, key, token):
    del data[key]
    response = send_request('post', PushNotificationServiceApi.CAMPAIGNS, token, data)
    assert response.status_code == 500
    response = response.json()
    error = response['error']
    assert error['code'] == 7003
    assert error['message'] == 'Some required fields are missing'
    assert error['missing_fields'] == [key]


def invalid_value_test(data, key, token, campaign_id):
    data.update(**generate_campaign_data())
    data[key] = ''
    response = send_request('put', '/v1/campaigns/%s' % campaign_id, token, data)
    response.status_code == 400, 'InvalidUsage exception raised'
    response = response.json()
    error = response['error']
    assert error['message'] == 'Invalid value for field in campaign data'
    assert error['field'] == key
    assert error['invalid_value'] == data[key]


def generate_campaign_data():
    """ Get random campaign data
    """
    data = {
        "title": fake.domain_name(),
        "content": fake.paragraph(1),
        "url": fake.url()
    }
    return data


def compare_campaign_data(campaign_obj, campaign_dict):
    _id = campaign_obj['id'] if isinstance(campaign_obj, dict) else campaign_obj.id
    content = campaign_obj['content'] if isinstance(campaign_obj, dict) else campaign_obj.content
    title = campaign_obj['title'] if isinstance(campaign_obj, dict) else campaign_obj.title
    url = campaign_obj['url'] if isinstance(campaign_obj, dict) else campaign_obj.url
    assert _id == campaign_dict['id']
    assert content == campaign_dict['content']
    assert title == campaign_dict['title']
    assert url == campaign_dict['url']
