import json
import time

import requests
from push_campaign_service.common.routes import PushNotificationServiceApi
from push_campaign_service.common.models.push_notification import *
from push_campaign_service.common.utils.models_utils import db

API_URL = PushNotificationServiceApi.HOST_NAME
VERSION = PushNotificationServiceApi.VERSION

SLEEP_TIME = 20
from push_campaign_service.tests.helper_methods import *


class TestCreateCampaign():

    # URL: /v1/campaigns [POST]
    def test_create_campaign(self, auth_data, campaign_data, test_campaign, test_smartlist):
        """
        This method tests push campaign creation endpoint.

        :param auth_data: token, validity_status
        :param campaign_data:
        :return:
        """
        token, is_valid = auth_data
        if is_valid:
            # First test with missing keys
            for key in ['title', 'content', 'url', 'smartlist_ids']:
                data = campaign_data.copy()
                data['smartlist_ids'] = [test_smartlist.id]
                missing_key_test(data, key, token)

            # Success case. Send a valid data and campaign should be created (201)
            data = campaign_data.copy()
            data['smartlist_ids'] = [test_smartlist.id]
            response = send_request('post', PushNotificationServiceApi.CAMPAIGNS, token, data)
            assert response.status_code == 201, 'Push campaign has been created'
            json_response = response.json()
            _id = json_response['id']
            assert json_response['message'] == 'Push campaign was created successfully'
            assert response.headers['Location'] == '%s%s/%s' % (PushNotificationServiceApi.HOST_NAME,
                                                                PushNotificationServiceApi.CAMPAIGNS,
                                                                _id)
            campaign_data['id'] = _id
        else:
            unauthorize_test('post', PushNotificationServiceApi.CAMPAIGNS, token, campaign_data)

    # URL: /v1/campaigns/ [GET]
    def test_get_list_of_zero_campaigns(self, auth_data):
        """
        This method tests get list of push campaign created by this user.
        At this point, test user has no campaign created, so we will get an empty list
        :param auth_data: token, validity_status
        :return:
        """
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushNotificationServiceApi.CAMPAIGNS, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()

            assert json_response['count'] == 0, 'Campaign Count should be 0 this time'
            assert len(json_response['campaigns']) == 0, 'Got an empty list of campaigns'
        else:
            unauthorize_test('get', PushNotificationServiceApi.CAMPAIGNS, token)

    # URL: /v1/campaigns [GET]
    def test_get_list_of_one_campaign(self, auth_data, test_campaign):
        """
        This method tests get list of push campaign created by this user.
        This time we will get one campaign in list that is created by `test_campaign` fixture
        :param auth_data: token, validity_status
        :type auth_data: tuple
        :param test_campaign: push campaign object
        :type test_campaign: PushCampaign
        :return:
        """
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', PushNotificationServiceApi.CAMPAIGNS, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()

            assert json_response['count'] == 1, 'Campaign Count should be 1 this time'
            assert len(json_response['campaigns']) == 1, 'Got one campaign in list'
            campaign = json_response['campaigns'][0]
            assert test_campaign.content == campaign['content']
            assert test_campaign.title == campaign['title']
            assert test_campaign.url == campaign['url']
        else:
            unauthorize_test('get', PushNotificationServiceApi.CAMPAIGNS, token)


class TestCampaignById():

    # URL: /v1/campaigns/:id [GET]
    def test_get_by_id(self, auth_data, test_campaign):
        token, is_valid = auth_data
        if is_valid:

            response = send_request('get', '/v1/campaigns/%s' % test_campaign.id, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()
            campaign = json_response['campaign']
            assert test_campaign.id == campaign['id']
            assert test_campaign.content == campaign['content']
            assert test_campaign.title == campaign['title']
            assert test_campaign.url == campaign['url']
        else:
            unauthorize_test('get', '/v1/campaigns/%s' % test_campaign.id, token)

    # update campaign test
    # URL: /v1/campaigns/:id [PUT]
    def test_put_by_id(self, auth_data, test_campaign, campaign_data, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            # First get already created campaign
            response = send_request('get', '/v1/campaigns/%s' % test_campaign.id, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()
            campaign = json_response['campaign']
            compare_campaign_data(test_campaign, campaign)

            # Test `raise InvalidUsage('No data given to be updated')`
            data = {}
            response = send_request('put', '/v1/campaigns/%s' % test_campaign.id, token, data)
            response.status_code == 400, 'InvalidUsage exception raised'
            assert response.json()['error']['message'] == 'No data given to be updated'

            # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
            data = campaign_data.copy()
            data['smartlist_ids'] = [test_smartlist.id]
            if 'user_id' in data: del data['user_id']
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            non_existing_id = last_obj.id + 1
            response = send_request('put', '/v1/campaigns/%s' % non_existing_id, token, data)
            response.status_code == 404, 'ResourceNotFound exception raised'
            assert response.json()['error']['message'] == 'Campaign not found with id %s' % non_existing_id

            # Test invalid field
            data.update(**generate_campaign_data())
            data['invalid_field_name'] = 'Any Value'
            response = send_request('put', '/v1/campaigns/%s' % test_campaign.id, token, data)
            response.status_code == 400, 'InvalidUsage exception raised'
            error = response.json()['error']
            assert error['message'] == 'Invalid field in campaign data'
            assert error['invalid_field'] == 'invalid_field_name'

            del data['invalid_field_name']
            smartlist_ids = data['smartlist_ids']

            # Test valid fields with invalid/ empty values
            for key in ['title', 'content', 'url', 'smartlist_ids']:
                invalid_value_test(data, key, token, test_campaign.id)

            # Test positive case with valid data
            data.update(**generate_campaign_data())
            data['smartlist_ids'] = smartlist_ids
            response = send_request('put', '/v1/campaigns/%s' % test_campaign.id, token, data)
            response.status_code == 200, 'Campaign updated successfully'
            data['id'] = test_campaign.id

            # Now get campaign from API and compare data.
            response = send_request('get', '/v1/campaigns/%s' % test_campaign.id, token)
            assert response.status_code == 200, 'Status code ok'
            json_response = response.json()
            campaign = json_response['campaign']
            # Compare sent campaign dict and campaign dict returned by API.
            compare_campaign_data(data, campaign)
        else:
            unauthorize_test('get', '/v1/campaigns/%s' % test_campaign.id, token)


class TestSendCmapign():

    # Send a campaign
    # URL: /v1/campaigns/<int:campaign_id>/send [POST]
    def test_send_a_camapign(self, auth_data, test_campaign, test_smartlist):
        token, is_valid = auth_data
        if is_valid:
            # 404 case. Send a non existing campaign id
            last_obj = PushCampaign.query.order_by(PushCampaign.id.desc()).first()
            response = send_request('post', '/v1/campaigns/%s/send' % (last_obj.id + 1), token)
            assert response.status_code == 404, 'Push campaign does not exists with this id'

            # 200 case: Campaign Sent successfully
            response = send_request('post', '/v1/campaigns/%s/send' % test_campaign.id, token)
            assert response.status_code == 200, 'Push campaign has been sent'
            response = response.json()
            assert response['message'] == 'Campaign(id:%s) is being sent to candidates' % test_campaign.id

            # Wait for 20 seconds to run celery which will send campaign and creates blast
            time.sleep(SLEEP_TIME)
            # Update session to get latest changes in database. Celery has added some records
            db.session.commit()
            # There should be only one blast for this campaign
            blasts = test_campaign.blasts.all()
            assert len(blasts) == 1
            assert test_campaign.blasts[0].sends == 1, 'Campaign was sent to one candidate'
        else:
            unauthorize_test('post', '/v1/campaigns/%s/send' % test_campaign.id, token)



