import json

import requests
from faker import Faker
from push_campaign_service.common.routes import PushCampaignApi, PushCampaignApiUrl

fake = Faker()


def send_request(method, url, access_token, data=None):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    return request_method(url, data=json.dumps(data),
                          headers={'Authorization': 'Bearer %s' % access_token,
                                   'Content-Type': 'application/json'})


def unauthorize_test(method, url, access_token, data=None):
    response = send_request(method, url, access_token,  data)
    assert response.status_code == 401, 'Access token is not valid'


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


def generate_campaign_data():
    """ Get random campaign data
    """
    data = {
        "name": fake.domain_name(),
        "body_text": fake.paragraph(1),
        "url": fake.url()
    }
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
