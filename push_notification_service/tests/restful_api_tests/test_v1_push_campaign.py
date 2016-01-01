import json

import requests
from push_notification_service.common.routes import PushNotificationServiceApi

API_URL = PushNotificationServiceApi.HOST_NAME


class TestCreateCampaign():
    def test_create_campaign(self, auth_data, campaign_data):
        """
        This method test push campaign creation endpoint.
        :param auth_data: token, validity_status
        :param campaign_data:
        :return:
        """
        token, is_valid = auth_data
        if is_valid:
            data = campaign_data.copy()
            del data['title']
            response = send_post_request('/v1/campaigns', data, token)
            assert response.status_code == 500
            response = response.json()
            assert response['error']['code'] == 7003
        else:
            unauthorize_test('post', PushNotificationServiceApi.CAMPAIGNS, token, campaign_data)


def send_post_request(relative_url, data, access_token):
    return requests.post(API_URL + relative_url, data=json.dumps(data),
                         headers={'Authorization': 'Bearer %s' % access_token,
                                  'Content-Type': 'application/json'})


def unauthorize_test(method, relative_url, access_token, data=None):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    response = request_method(API_URL + relative_url, data=json.dumps(data),
                              headers={'Authorization': 'Bearer %s' % access_token,
                                       'Content-Type': 'application/json'})
    assert response.status_code == 401, 'Access token is not valid'
