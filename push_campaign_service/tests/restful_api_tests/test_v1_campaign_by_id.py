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
        unauthorize_test('get', URL % campaign_in_db.id, 'invalid_token')

    def test_get_by_id(self, token, campaign_in_db):

        response = send_request('get', URL % campaign_in_db.id, token)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        assert campaign_in_db.id == campaign['id']
        assert campaign_in_db.body_text == campaign['body_text']
        assert campaign_in_db.name == campaign['name']
        assert campaign_in_db.url == campaign['url']


class TestUpdateCampaign(object):
    # update campaign test
    # URL: /v1/campaigns/:id [PUT]
    def test_put_by_id_with_invalid_token(self, campaign_in_db, test_smartlist):
        data = generate_campaign_data()
        data['smartlist_ids'] = [test_smartlist.id]
        unauthorize_test('put', URL % campaign_in_db.id,
                         'invalid_token', data)

    def test_put_by_id_without_ownership(self, token2, campaign_in_db, test_smartlist):
        # Test `raise ForbiddenError`
        data = generate_campaign_data()
        data['smartlist_ids'] = [test_smartlist.id]
        response = send_request('put', URL % campaign_in_db.id, token2, data)
        assert response.status_code == FORBIDDEN

    def test_put_by_id_with_invalid_id(self, token, test_smartlist):
        # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
        data = generate_campaign_data()
        data['smartlist_ids'] = [test_smartlist.id]
        invalid_id = get_non_existing_id(PushCampaign)
        for _id in [0, invalid_id]:
            response = send_request('put', URL % _id, token, data)
            assert response.status_code == NOT_FOUND, 'ResourceNotFound exception should be raised'

    def test_put_by_id_with_invalid_field(self, token, campaign_in_db, test_smartlist):
        # Test invalid field
        data = generate_campaign_data()
        data['invalid_field_name'] = 'Any Value'
        response = send_request('put', URL % campaign_in_db.id, token, data)
        assert response.status_code == INVALID_USAGE, 'InvalidUsage exception should be raised'
        error = response.json()['error']
        assert error['invalid_field'] == 'invalid_field_name'

    def test_put_by_id_with_missing_required_key(self, token, test_smartlist, campaign_in_db):
        # Test valid fields with invalid/ empty values
        data = generate_campaign_data()
        data['smartlist_ids'] = [test_smartlist.id]
        for key in ['name', 'body_text', 'url', 'smartlist_ids']:
            invalid_value_test(data, key, token, campaign_in_db.id)

    def test_put_by_id(self, token, campaign_in_db, campaign_data, test_smartlist):
        # Test positive case with valid data
        data = generate_campaign_data()
        data['smartlist_ids'] = [test_smartlist.id]
        response = send_request('put', URL % campaign_in_db.id, token, data)
        assert response.status_code == OK, 'Campaign was not updated successfully'
        data['id'] = campaign_in_db.id

        # Now get campaign from API and compare data.
        response = send_request('get', URL % campaign_in_db.id, token)
        assert response.status_code == OK, 'Status code is not 200'
        json_response = response.json()
        campaign = json_response['campaign']
        # Compare sent campaign dict and campaign dict returned by API.
        compare_campaign_data(data, campaign)


class TestCampaignDeleteById(object):
    # Test URL: /v1/campaigns/<int:id> [DELETE]
    def test_delete_campaign_with_invalid_token(self, campaign_in_db):
        """
        Hit the url with invalid authentication token and it should
        raise Unauthorized Error 401
        :param campaign_in_db: push campaign object created by fixture
        :return:
        """
        # We are testing 401 here
        unauthorize_test('delete',  URL % campaign_in_db.id,
                         'invalid_token')

    def test_delete_non_existing_campaign(self, token):
        """
        Test that if someone wants to delete a campaign that does not exists,
        it should raise ResourceNotFound 404
        :param token: auth token
        :return:
        """
        non_existing_campaign_id = get_non_existing_id(PushCampaign)
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % non_existing_campaign_id, token)
        assert response.status_code == NOT_FOUND, 'Resource should not be found'

    def test_delete_campaign_with_invalid_id(self, token):
        """
        Test if someone passes an invalid value like 0, it should raise InvalidUsage
        :param token: auth token
        :return:
        """
        invalid_id = 0
        response = send_request('delete', URL % invalid_id, token)
        assert response.status_code == INVALID_USAGE, 'Resource should not be found'

    def test_delete_campaign_without_ownership(self, token2, campaign_in_db):
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % campaign_in_db.id, token2)
        assert response.status_code == FORBIDDEN

    def test_delete_unscheduled_campaign(self, token, campaign_in_db):
        """
        Try deleting a campaign that is not scheduled yet and it should
        successfully delete
        :param token:
        :param campaign_in_db:
        :return:
        """
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % campaign_in_db.id, token)
        assert response.status_code == OK

    def test_delete_scheduled_campaign(self, token, campaign_in_db, schedule_a_campaign):
        # 404 Case, Campaign not found
        # 404 with invalid campaign id and valid blast id
        response = send_request('delete', URL % campaign_in_db.id, token)
        assert response.status_code == OK
