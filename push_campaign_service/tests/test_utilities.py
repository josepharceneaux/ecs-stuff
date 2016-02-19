import json
from datetime import datetime, timedelta
import requests
from faker import Faker

from push_campaign_service.common.campaign_services.custom_errors import CampaignException
from push_campaign_service.common.models.push_campaign import PushCampaignSmartlist
from push_campaign_service.common.models.smartlist import Smartlist, SmartlistCandidate
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi, \
    UserServiceApiUrl
from push_campaign_service.common.utils.handy_functions import to_utc_str

fake = Faker()

API_URL = PushCampaignApiUrl.HOST_NAME
VERSION = PushCampaignApi.VERSION
SLEEP_TIME = 20
OK = 200
INVALID_USAGE = 400
NOT_FOUND = 404
FORBIDDEN = 403
INTERNAL_SERVER_ERROR = 500


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
    assert response.status_code == INVALID_USAGE
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
    response.status_code == INVALID_USAGE
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
    assert response.status_code == INVALID_USAGE
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == INVALID_USAGE
    data = {}
    response = send_request(method, url, token, data, is_json=True)
    assert response.status_code == INVALID_USAGE
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == INVALID_USAGE
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    assert response.status_code == INVALID_USAGE


def generate_campaign_data():
    """ Generates random campaign data
    :return data
    :rtype dict
    """
    data = {
        "name": fake.domain_name(),
        "body_text": fake.paragraph(1),
        "url": 'https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-getting-started' #fake.url()
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
    """
    This function compares a push campaign object and a campaign data dictionary.
    It raises assertion error if respective keys do not match.
    :param campaign_obj: push campaign model instance
    :param campaign_dict: campaign data
    :type campaign_obj: PushCampaign
    :type campaign_dict: dict
    :return:
    """
    _id = campaign_obj['id'] if isinstance(campaign_obj, dict) else campaign_obj.id
    body_text = campaign_obj['body_text'] if isinstance(campaign_obj, dict) else campaign_obj.body_text
    name = campaign_obj['name'] if isinstance(campaign_obj, dict) else campaign_obj.name
    url = campaign_obj['url'] if isinstance(campaign_obj, dict) else campaign_obj.url
    assert _id == campaign_dict['id']
    assert body_text == campaign_dict['body_text']
    assert name == campaign_dict['name']
    assert url == campaign_dict['url']


def get_non_existing_id(model):
    """
    This functions takes a model class and returns a non existing id
    by getting last object and then adding a large number in it and
    if table is empty, simply return that number
    :param model:
    :return: non_existing_id
    :rtype int | long
    """
    last_obj = model.query.order_by(model.id.desc()).first()
    if last_obj:
        return last_obj.id + 1000
    else:
        return 1000


def create_smart_list(request, sample_user, test_candidate, test_candidate_device, campaign_in_db):
    """
    This function associates smartlist with push campaign.
    :param request: request object
    :param sample_user: test user to use api
    :param test_candidate: test candidate to whom campaign will be sent
    :param test_candidate_device: device associated with candidate
    :param campaign_in_db: push campaign object
    :return:
    """
    smartlist = Smartlist(user_id=sample_user.id,
                          name=fake.word())
    Smartlist.save(smartlist)

    smartlist_candidate = SmartlistCandidate(candidate_id=test_candidate.id,
                                             smartlist_id=smartlist.id)
    SmartlistCandidate.save(smartlist_candidate)

    push_smartlist = PushCampaignSmartlist(smartlist_id=smartlist.id,
                                           campaign_id=campaign_in_db.id)
    PushCampaignSmartlist.save(push_smartlist)
    return smartlist


def add_roles(user_id, roles, token):
    """
    This method sends a POST request to UserService to add given roles to given user
    :param user_id: id of user
    :param roles: permissions list
    :param token: auth token
    :return: True | False
    """
    data = {
        "roles": roles
    }
    response = send_request('post', UserServiceApiUrl.USER_ROLES_API % user_id,
                            token, data=data)
    if response.status_code == 400 and response.json()['error']['code'] == 9000:
        return None
    assert response.status_code == 200


def remove_roles(user_id, roles, token):
    """
    This method sends a DELETE request to UserService to remove given roles to given user
    :param user_id: id of user
    :param roles: permissions list
    :param token: auth token
    :return: True | False
    """
    data = {
        "roles": roles
    }
    response = send_request('delete', UserServiceApiUrl.USER_ROLES_API % user_id,
                            token, data=data)
    assert response.status_code == 200

