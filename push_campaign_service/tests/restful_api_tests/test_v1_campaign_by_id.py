"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl

URL = PushCampaignApiUrl.CAMPAIGN


class TestCampaignById(object):

    # URL: /v1/campaigns/:id [GET]
    def test_get_by_id_with_invalid_token(self, campaign_in_db):
        unauthorize_test('get', URL % campaign_in_db['id'], 'invalid_token')

    def test_get_by_id(self, token_first, campaign_in_db):

        response = send_request('get', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        assert campaign_in_db['id'] == campaign['id']
        assert campaign_in_db['body_text'] == campaign['body_text']
        assert campaign_in_db['name'] == campaign['name']
        assert campaign_in_db['url'] == campaign['url']


class TestUpdateCampaign(object):
    # update campaign test
    # URL: /v1/campaigns/:id [PUT]
    def test_put_by_id_with_invalid_token(self, campaign_in_db, smartlist_first):
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        unauthorize_test('put', URL % campaign_in_db['id'],
                         'invalid_token', data)

    def test_put_by_id_without_ownership(self, token_second, campaign_in_db, smartlist_first):
        # Test `raise ForbiddenError`
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        response = send_request('put', URL % campaign_in_db['id'], token_second, data)
        assert response.status_code == FORBIDDEN

    def test_put_by_id_with_invalid_id(self, token_first, smartlist_first, campaign_in_db):
        # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        invalid_id = campaign_in_db['id'] + 10000
        for _id in [0, invalid_id]:
            response = send_request('put', URL % _id, token_first, data)
            assert response.status_code == NOT_FOUND, 'ResourceNotFound exception should be raised'

    def test_put_by_id_with_invalid_field(self, token_first, campaign_in_db, smartlist_first):
        # Test invalid field
        data = generate_campaign_data()
        data['invalid_field_name'] = 'Any Value'
        response = send_request('put', URL % campaign_in_db['id'], token_first, data)
        assert response.status_code == INVALID_USAGE, 'InvalidUsage exception should be raised'
        error = response.json()['error']
        assert error['invalid_field'] == 'invalid_field_name'

    def test_put_by_id_with_missing_required_key(self, token_first, smartlist_first, campaign_in_db):
        # Test valid fields with invalid/ empty values
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        for key in ['name', 'body_text', 'url', 'smartlist_ids']:
            invalid_value_test(data, key, token_first, campaign_in_db['id'])

    def test_put_by_id(self, token_first, campaign_in_db, campaign_data, smartlist_first):
        # Test positive case with valid data
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        response = send_request('put', URL % campaign_in_db['id'], token_first, data)
        assert response.status_code == OK, 'Campaign was not updated successfully'
        data['id'] = campaign_in_db['id']

        # Now get campaign from API and compare data.
        response = send_request('get', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        # Compare sent campaign dict and campaign dict returned by API.
        compare_campaign_data(data, campaign)


class TestCampaignDeleteById(object):
    # Test URL: /v1/campaigns/<int:id> [DELETE]
    def test_delete_campaign_with_invalid_token(self, campaign_in_db):
        """
        Hit the url with invalid authentication token_first and it should
        raise Unauthorized Error 401
        :param campaign_in_db: push campaign object created by fixture
        :return:
        """
        # We are testing 401 here
        unauthorize_test('delete',  URL % campaign_in_db['id'],
                         'invalid_token')

    def test_delete_non_existing_campaign(self, token_first, campaign_in_db):
        """
        Test that if someone wants to delete a campaign that does not exists,
        it should raise ResourceNotFound 404
        :param token_first: auth token_first
        :return:
        """
        non_existing_campaign_id = campaign_in_db['id'] + 10000
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % non_existing_campaign_id, token_first)
        assert response.status_code == NOT_FOUND, 'Resource should not be found'

    def test_delete_campaign_with_invalid_id(self, token_first):
        """
        Test if someone passes an invalid value like 0, it should raise InvalidUsage
        :param token_first: auth token_first
        :return:
        """
        invalid_id = 0
        response = send_request('delete', URL % invalid_id, token_first)
        assert response.status_code == INVALID_USAGE, 'Resource should not be found'

    def test_delete_campaign_without_ownership(self, token_second, campaign_in_db):
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % campaign_in_db['id'], token_second)
        assert response.status_code == FORBIDDEN

    def test_delete_unscheduled_campaign(self, token_first, campaign_in_db):
        """
        Try deleting a campaign that is not scheduled yet and it should
        successfully delete
        :param token_first:
        :param campaign_in_db:
        :return:
        """
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK

    def test_delete_scheduled_campaign(self, token_first, campaign_in_db, schedule_a_campaign):
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % campaign_in_db['id'], token_first)
        assert response.status_code == OK
