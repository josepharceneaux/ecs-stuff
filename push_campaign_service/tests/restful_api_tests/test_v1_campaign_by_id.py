"""
This module contains test for API endpoint
        /v1/push-campaigns/:id

In these tests, we will try to update, get and delete a specific campaign
in different scenarios like:

Update Campaign: /v1/push-campaigns/:id [PUT]
    - with invalid token
    - that is created by user from different domain (403)
    - with invalid fields in data
    - with missing required fields in data
    - with valid data
    - that does not exist (invalid campaign id)
    - with valid data (200)

Get Campaign: /v1/push-campaigns/:id [GET]
    - with invalid token
    - with valid token

Delete a Campaign: /v1/push-campaigns/:id [DELETE]
    - with invalid token
    - with valid token
    - with invalid campaign id
    - that belongs to a user from different domain
    - that belongs to user from same domain
    - that is not yet scheduled
    - that is scheduled
"""

# Builtin imports
import sys

# 3rd party imports
from requests import codes

# Application specific imports
from push_campaign_service.tests.test_utilities import (get_campaign,delete_campaign, invalid_value_test,
                                                        compare_campaign_data, generate_campaign_data, update_campaign)
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.utils.test_utils import unauthorize_test
from push_campaign_service.modules.constants import CAMPAIGN_REQUIRED_FIELDS


URL = PushCampaignApiUrl.CAMPAIGN


class TestCampaignById(object):

    # URL: /v1/push-campaigns/:id [GET]
    def test_get_by_id_with_invalid_token(self, campaign_in_db):
        """
        We will try to get a valid campaign with invalid token and api will raise
        Unauthorized 401 error
        :param campaign_in_db: campaign object
        """
        get_campaign(campaign_in_db['id'], 'invalid_token', expected_status=(401,))

    def test_get_by_id(self, token_first, campaign_in_db):
        """
        We will try to get campaign with a valid token and we are expecting OK (200) response
        :param token_first: auth token
        :param campaign_in_db: campaign object
        """
        json_response = get_campaign(campaign_in_db['id'], token_first)
        campaign = json_response['campaign']
        assert campaign_in_db['id'] == campaign['id']
        assert campaign_in_db['body_text'] == campaign['body_text']
        assert campaign_in_db['name'] == campaign['name']
        assert campaign_in_db['url'] == campaign['url']

    def test_get_campaign_with_invalid_id(self, token_first):
        """
        In this test, we will try to get a campaign that does not exists.
        We are expecting 404 here.
        :param token_first: auth token
        """
        campaign_id = sys.maxint
        get_campaign(campaign_id, token_first, expected_status=(404,))

    def test_get_deleted_campaign(self, token_first, campaign_in_db):
        """
        In this test, we will try to get a campaign that does not exists.
        We are expecting 404 here.
        :param token_first: auth token
        """
        campaign_id = campaign_in_db['id']
        delete_campaign(campaign_id, token_first)
        get_campaign(campaign_id, token_first, expected_status=(404,))

    def test_get_campaign_from_same_domain(self, token_same_domain, campaign_in_db):
        """
        We will try to get campaign with a valid token. User is not owner of campaign
         and he is from same domain as the owner of the campaign. We are expecting OK (200) response.
        :param token_same_domain: auth token
        :param campaign_in_db: campaign object
        """
        campaign_id = campaign_in_db['id']
        json_response = get_campaign(campaign_id, token_same_domain, expected_status=(200,))
        campaign = json_response['campaign']
        assert campaign_in_db['id'] == campaign['id']
        assert campaign_in_db['body_text'] == campaign['body_text']
        assert campaign_in_db['name'] == campaign['name']
        assert campaign_in_db['url'] == campaign['url']

    def test_get_campaign_from_diff_domain(self, token_second, campaign_in_db):
        """
        We will try to get campaign with a valid token. User is not owner of campaign
         and he is from same domain as the owner of the campaign. We are expecting OK (200) response.
        :param token_second: auth token
        :param campaign_in_db: campaign object
        """
        campaign_id = campaign_in_db['id']
        get_campaign(campaign_id, token_second, expected_status=(403,))


class TestUpdateCampaign(object):
    # update campaign test
    # URL: /v1/push-campaigns/:id [PUT]
    def test_put_by_id_with_invalid_token(self, campaign_in_db, smartlist_first):
        """
        Try to update a campaign with invalid token and API will raise Unauthorized (401) error
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist object
        """
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        unauthorize_test('put', URL % campaign_in_db['id'], data)

    def test_update_campaign_from_diff_domain(self, token_second, campaign_in_db, smartlist_first):
        """
        We will try to update a campaign but user is not owner and from a different domain,
        so we are expecting Forbidden (403) error
        :param token_second: auth token
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist object
        """
        # Test `raise ForbiddenError`
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        campaign_id = campaign_in_db['id']
        update_campaign(campaign_id, data, token_second, expected_status=(codes.FORBIDDEN,))

    def test_update_campaign_with_invalid_id(self, token_first, smartlist_first):
        """
        Try to update a campaign that does not exist, API will raise ResourceNotFound (404) error
        :param token_first: auth token
        :param smartlist_first: smartlist object
        """
        # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        invalid_id = sys.maxint
        for _id in [0, invalid_id]:
            update_campaign(_id, data, token_first, expected_status=(codes.NOT_FOUND,))

    def test_update_deleted_campaign(self, token_first, campaign_in_db, smartlist_first):
        """
        Try to update a campaign that has been delete, API will raise ResourceNotFound (404) error
        :param token_first: auth token
        :param smartlist_first: smartlist object
        :param campaign_in_db: campaign object
        """
        # Test `raise ResourceNotFound('Campaign not found with id %s' % campaign_id)`
        campaign_id = campaign_in_db['id']
        delete_campaign(campaign_id, token_first)
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        update_campaign(campaign_id, data, token_first, expected_status=(codes.NOT_FOUND,))

    def test_update_campaign_with_invalid_field(self, token_first, campaign_in_db, smartlist_first):
        """
        Try to update a campaign with an invalid key in campaign data , API will raise
        InvalidUsage (400) error
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist object
        """
        # Test invalid field
        data = generate_campaign_data()
        data['invalid_field_name'] = 'Any Value'
        campaign_id = campaign_in_db['id']
        response = update_campaign(campaign_id, data, token_first,
                                   expected_status=(codes.BAD_REQUEST,))
        error = response['error']
        assert error['invalid_field'] == 'invalid_field_name'

    def test_put_by_id_with_missing_required_key(self, token_first, smartlist_first, campaign_in_db):
        """
        Try to update a campaign with some required field missing, and API will raise
        InvalidUsage (400) error
        :param token_first: auth token
        :param smartlist_first: smartlist object
        :param campaign_in_db: campaign object
        """
        # Test valid fields with invalid/ empty values
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        for key in CAMPAIGN_REQUIRED_FIELDS:
            invalid_value_test(data, key, token_first, campaign_in_db['id'])

    def test_put_by_id(self, token_first, campaign_in_db, smartlist_first):
        """
        Try to update a campaign with valid data, we are expecting that API will
        update the campaign successfully (200)
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param smartlist_first: smartlist object
        """
        # Test positive case with valid data
        data = generate_campaign_data()
        data['smartlist_ids'] = [smartlist_first['id']]
        campaign_id = campaign_in_db['id']
        update_campaign(campaign_id, data, token_first, expected_status=(codes.OK,))

        # Now get campaign from API and compare data.
        json_response = get_campaign(campaign_id, token_first)
        campaign = json_response['campaign']
        # Compare sent campaign dict and campaign dict returned by API.
        compare_campaign_data(data, campaign)


class TestCampaignDeleteById(object):
    # Test URL: /v1/push-campaigns/<int:id> [DELETE]
    def test_delete_campaign_with_invalid_token(self, campaign_in_db):
        """
        Hit the url with invalid authentication token_first and it should
        raise Unauthorized Error 401
        :param campaign_in_db: push campaign object created by fixture
        """
        # We are testing 401 here
        unauthorize_test('delete',  URL % campaign_in_db['id'])

    def test_delete_non_existing_campaign(self, token_first):
        """
        Test that if someone wants to delete a campaign that does not exists,
        it should raise ResourceNotFound 404
        :param token_first: auth token_first
        """
        non_existing_campaign_id = sys.maxint
        # 404 Case, Campaign not found
        delete_campaign(non_existing_campaign_id, token_first,
                        expected_status=(codes.NOT_FOUND,))

    def test_delete_campaign_with_invalid_id(self, token_first):
        """
        Test if someone passes an invalid value like 0, it should raise InvalidUsage
        :param token_first: auth token_first
        """
        invalid_id = 0
        delete_campaign(invalid_id, token_first, expected_status=(codes.BAD_REQUEST,))

    def test_delete_campaign_with_user_from_same_domain(self, token_same_domain, campaign_in_db):
        """
        Try to delete a campaign but the user is not owner of given campaign but from
         same domain So API should allow him to do so (200)
        :param token_same_domain: auth token
        :param campaign_in_db: campaign object
        """
        delete_campaign(campaign_in_db['id'], token_same_domain, expected_status=(codes.OK,))

    def test_delete_campaign_from_diff_domain(self, token_second, campaign_in_db):
        """
        Try to delete a campaign but the user is not owner of given campaign and
        he is from different domain. So API should not allow (403)
        :param token_second: auth token
        :param campaign_in_db: campaign object
        """
        delete_campaign(campaign_in_db['id'], token_second, expected_status=(codes.FORBIDDEN,))

    def test_delete_unscheduled_campaign(self, token_first, campaign_in_db):
        """
        Try deleting a campaign that is not scheduled yet and it should
        successfully delete
        :param token_first: auth token
        :param campaign_in_db: campaign object
        """
        # 200 Case, Campaign not found
        delete_campaign(campaign_in_db['id'], token_first, expected_status=(codes.OK,))

    def test_delete_scheduled_campaign(self, token_first, campaign_in_db, schedule_a_campaign):
        """
        Try to delete a scheduled campaign , API should successfully delete that campaign
        :param token_first: auth token
        :param campaign_in_db: campaign object
        :param schedule_a_campaign: fixture to schedule a campaign
        """
        delete_campaign(campaign_in_db['id'], token_first, expected_status=(codes.OK,))
