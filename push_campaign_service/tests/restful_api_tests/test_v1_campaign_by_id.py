"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports

# Application specific imports
from push_campaign_service.tests.helper_methods import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl, PushCampaignApi
# Constants
API_URL = PushCampaignApi.HOST_NAME
VERSION = PushCampaignApi.VERSION

SLEEP_TIME = 20
OK = 200
INVALID_USAGE = 400
NOT_FOUND = 404
FORBIDDEN = 403
INTERNAL_SERVER_ERROR = 500


class TestCampaignById(object):

    # URL: /v1/campaigns/:id [GET]
    def test_get_by_id_with_invalid_token(self, campaign_in_db):
        unauthorize_test('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, 'invalid_token')

    def test_get_by_id(self, token, campaign_in_db):

        response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        assert campaign_in_db.id == campaign['id']
        assert campaign_in_db.body_text == campaign['body_text']
        assert campaign_in_db.name == campaign['name']
        assert campaign_in_db.url == campaign['url']

    # update campaign test
    # URL: /v1/campaigns/:id [PUT]
    def test_put_by_id_with_invalid_id(self,campaign_in_db):
        unauthorize_test('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, 'invalid_data')

    def test_put_by_id(self, token, campaign_in_db, campaign_data, test_smartlist):

        # First get already created campaign
        response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        compare_campaign_data(campaign_in_db, campaign)
        invalid_data_test('put', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)

        # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
        data = generate_campaign_data()
        data['smartlist_ids'] = [test_smartlist.id]
        last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
        for _id in [0, last_obj.id + 100]:
            response = send_request('put', PushCampaignApiUrl.CAMPAIGN % _id, token, data)
            assert response.status_code == NOT_FOUND, 'ResourceNotFound exception should be raised'
            assert response.json()['error']['message'] == 'Campaign not found with id %s' % _id

        # Test invalid field
        data.update(**generate_campaign_data())
        data['invalid_field_name'] = 'Any Value'
        response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE, 'InvalidUsage exception should be raised'
        error = response.json()['error']
        assert error['message'] == 'Invalid field in campaign data'
        assert error['invalid_field'] == 'invalid_field_name'

        del data['invalid_field_name']
        smartlist_ids = data['smartlist_ids']

        # Test valid fields with invalid/ empty values
        for key in ['name', 'body_text', 'url', 'smartlist_ids']:
            invalid_value_test(data, key, token, campaign_in_db.id)

        # Test positive case with valid data
        data.update(**generate_campaign_data())
        data['smartlist_ids'] = smartlist_ids
        response = send_request('put', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token, data)
        assert response.status_code == OK, 'Campaign was not updated successfully'
        data['id'] = campaign_in_db.id

        # Now get campaign from API and compare data.
        response = send_request('get', PushCampaignApiUrl.CAMPAIGN % campaign_in_db.id, token)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        # Compare sent campaign dict and campaign dict returned by API.
        compare_campaign_data(data, campaign)