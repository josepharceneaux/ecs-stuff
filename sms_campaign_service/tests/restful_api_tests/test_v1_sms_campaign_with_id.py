"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id of SMS Campaign API.
"""
# Standard Imports
import json

# Third Party
import requests

# Service Specific
from email_campaign_service.common.custom_errors.campaign import EMAIL_CAMPAIGN_FORBIDDEN
from sms_campaign_service.modules.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import (assert_campaign_delete, assert_valid_campaign_get,
                                                                 generate_campaign_data)

# Common Utils
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from sms_campaign_service.common.error_handling import (UnauthorizedError, ForbiddenError, InvalidUsage)


class TestSmsCampaignWithIdHTTPGET(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method GET.

    """
    HTTP_METHOD = 'get'
    URL = SmsCampaignApiUrl.CAMPAIGN

    def test_with_invalid_token(self, sms_campaign_of_user_first):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD,
                                                         self.URL % sms_campaign_of_user_first['id'])

    def test_get_campaign_in_same_domain(self, data_for_different_users_of_same_domain,
                                         sms_campaign_of_user_first):
        """
        User auth token is valid. It uses 'sms_campaign_of_user_first' fixture
        to create an SMS campaign in database. It gets that record from GET HTTP request
        Response should be OK. It then assert all fields of record that we get from GET call with the
        original field values (provided at time of creation of campaign).
        This runs for both users
        1) Who created the campaign and 2) Some other user of same domain
        """
        access_token = data_for_different_users_of_same_domain['access_token']
        response = requests.get(self.URL % sms_campaign_of_user_first['id'],
                                headers=dict(Authorization='Bearer %s' % access_token))
        assert response.status_code == requests.codes.OK, 'Response should be ok (200)'
        received_campaign = response.json()['campaign']
        # verify values of all the fields
        assert_valid_campaign_get(received_campaign, sms_campaign_of_user_first)

    def test_get_campaign_present_in_other_domain(self, access_token_first, sms_campaign_in_other_domain):
        """
        User auth token is valid. It uses 'sms_campaign_in_other_domain' fixture
        to create an SMS campaign in database. It gets that record from GET HTTP request
        Response should result in Forbidden error as campaign does not belong to domain of logged-in user.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % sms_campaign_in_other_domain['id'],
                                                          access_token_first,
                                                          expected_error_code=EMAIL_CAMPAIGN_FORBIDDEN[1])

    def test_get_deleted_campaign(self, access_token_first, sms_campaign_of_user_first):
        """
        User auth token is valid. It deletes the campaign and then GETs the record from db.
        It should result in ResourceNotFound error.
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_user_first,
                                                              self.URL,
                                                              self.URL, self.HTTP_METHOD,
                                                              access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get campaign object with invalid resource id.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign, self.HTTP_METHOD, self.URL,
                                                               access_token_first)


class TestSmsCampaignWithIdHTTPPUT(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method POST.
    """
    HTTP_METHOD = 'put'
    URL = SmsCampaignApiUrl.CAMPAIGN

    def test_with_invalid_token(self, sms_campaign_of_user_first):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'])

    def test_with_invalid_header(self, access_token_first, sms_campaign_of_user_first):
        """
        User auth token is valid, but content-type is not set.
        it should get bad request error.
        """
        response = requests.put(self.URL % sms_campaign_of_user_first['id'],
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == InvalidUsage.http_status_code(), 'It should be a bad request (400)'

    def test_updating_campaign_in_same_domain(self, data_for_different_users_of_same_domain,
                                              campaign_valid_data, sms_campaign_of_user_first):
        """
        This uses fixture to create an sms_campaign record in db. It then makes a PUT
        call to update that record with name modification. If status code is 200, it then
        gets the record from database and assert the 'name' of modified record.
        """
        headers = data_for_different_users_of_same_domain['headers']
        data = campaign_valid_data.copy()
        modified_name = 'Modified Name'
        data.update({'name': modified_name})
        response = requests.put(self.URL % sms_campaign_of_user_first['id'], headers=headers, data=json.dumps(data))
        assert response.status_code == requests.codes.OK, response.json()['error']['message']

        # get updated record to verify the change we made in name
        response_get = requests.get(self.URL % sms_campaign_of_user_first['id'], headers=headers)
        assert response_get.status_code == requests.codes.OK, response_get.json()['error']['message']
        resp = response_get.json()['campaign']
        assert resp
        assert resp['name'] == modified_name

    def test_updating_sms_campaign_of_other_domain(self, headers, sms_campaign_in_other_domain, campaign_valid_data):
        """
        Here we try to update a campaign which does not belong to domain of logged-in user.
        It should get forbidden error.

        This runs for both users
        1) Who created the campaign and 2) Some other user of same domain
        """
        modified_name = 'Modified Name'
        campaign_valid_data.update({'name': modified_name})
        response_post = requests.put(self.URL % sms_campaign_in_other_domain['id'], headers=headers,
                                     data=json.dumps(campaign_valid_data))
        CampaignsTestsHelpers.assert_non_ok_response(response_post, ForbiddenError.http_status_code())

    def test_updating_deleted_record(self, sms_campaign_of_user_first, campaign_valid_data, access_token_first):
        """
        User auth token is valid. It deletes the campaign from database and then tries
        to update the record. It should result in ResourceNotFound error.
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_user_first, self.URL,
                                                              self.URL, self.HTTP_METHOD, access_token_first,
                                                              campaign_valid_data)

    def test_campaign_update_with_deleted_or_hidden_smartlist_id(self, sms_campaign_of_user_first, campaign_valid_data,
                                                                 access_token_first):
        """
        Update campaign with deleted smartlist , API should raise InvalidUsage 400
        """
        smartlist_id = sms_campaign_of_user_first['smartlist_ids'][0]
        url = self.URL % sms_campaign_of_user_first['id']
        campaign_valid_data['smartlist_ids'] = [smartlist_id]
        # Create a campaign with deleted smartlist. API will raise 400 error.
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, url, access_token_first,
                                                                  smartlist_id, campaign_valid_data)

    def test_with_no_data(self, headers, sms_campaign_of_user_first):
        """
        User auth token is valid but no data is provided. It should get bad request error.
        """
        response = requests.put(self.URL % sms_campaign_of_user_first['id'], headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_with_non_json_data(self, headers, campaign_valid_data, sms_campaign_of_user_first):
        """
        This tries to update SMS campaign record (in sms_campaign table) providing data in dict
        format rather than JSON. It should get bad request error.
        """
        response = requests.put(self.URL % sms_campaign_of_user_first['id'], headers=headers, data=campaign_valid_data)
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_with_missing_required_fields(self, headers, sms_campaign_of_user_first,
                                          invalid_data_for_campaign_creation):
        """
        It tries to update the already present sms_campaign record with invalid_data.
        We pass data with missing required keys. It should get bad request error.
        """
        campaign_data, missing_key = invalid_data_for_campaign_creation
        response = requests.put(self.URL % sms_campaign_of_user_first['id'], headers=headers,
                                data=json.dumps(campaign_data))
        assert response.status_code == InvalidUsage.http_status_code(), 'It should get bad request error'
        assert missing_key in response.json()['error']['message']

    def test_campaign_update_with_unexpected_field_in_data(self, campaign_valid_data, access_token_first,
                                                           sms_campaign_of_user_first):
        """
        User has one phone value, headers are valid and sms-campaign is being updated with
        invalid data (having some unexpected fields). It should result in Invalid usage error.
        """
        CampaignsTestsHelpers.test_api_with_with_unexpected_field_in_data(
            self.HTTP_METHOD, self.URL % sms_campaign_of_user_first['id'], access_token_first, campaign_valid_data)

    def test_campaign_update_with_invalid_campaign_name(self, access_token_first, campaign_valid_data,
                                                        sms_campaign_of_user_first):
        """
        This is a test to update SMS campaign with invalid campaign name. Status code should be 400 and
        campaign should not be updated.
        """
        CampaignsTestsHelpers.request_with_invalid_string(self.HTTP_METHOD,
                                                                            self.URL % sms_campaign_of_user_first['id'],
                                                                            access_token_first,
                                                                            campaign_valid_data.copy(), 'name')

    def test_campaign_update_with_invalid_body_text(self, access_token_first, campaign_valid_data,
                                                    sms_campaign_of_user_first):
        """
        This is a test to update SMS campaign with invalid body_text. Status code should be 400 and
        campaign should not be updated.
        """
        CampaignsTestsHelpers.request_with_invalid_string(self.HTTP_METHOD,
                                                                            self.URL % sms_campaign_of_user_first['id'],
                                                                            access_token_first,
                                                                            campaign_valid_data.copy(), 'body_text')

    def test_campaign_update_with_invalid_smartlists_ids(self, access_token_first, sms_campaign_of_user_first):
        """
        This is a test to update a campaign with invalid smartlist Ids. It should result in InvalidUsage error.
        """
        CampaignsTestsHelpers.campaign_create_or_update_with_invalid_smartlist(
            self.HTTP_METHOD,  self.URL % sms_campaign_of_user_first['id'],  access_token_first,
            generate_campaign_data())

    def test_campaign_update_with_valid_and_not_owned_smartlist_ids(self, headers, campaign_valid_data,
                                                                    smartlist_with_two_candidates_in_other_domain,
                                                                    sms_campaign_of_user_first):
        """
        This is a test to update a campaign with smartlist id of some other domain. It should result in
        ForbiddenError.
        """
        data = campaign_valid_data.copy()
        data['smartlist_ids'].extend([smartlist_with_two_candidates_in_other_domain[0]])
        response = requests.put(self.URL % sms_campaign_of_user_first['id'], headers=headers, data=json.dumps(data))
        CampaignsTestsHelpers.assert_non_ok_response(response, ForbiddenError.http_status_code())

    def test_campaign_update_with_invalid_url_in_body_text(self, campaign_valid_data, headers,
                                                           sms_campaign_of_user_first):
        """
        User has one mobile number, valid header and invalid URL in body text(random word).
        It should get invalid usage error, Custom error should be INVALID_URL_FORMAT.
        """
        campaign_valid_data['body_text'] += 'http://' + fake.word()
        response = requests.put(self.URL % sms_campaign_of_user_first['id'], headers=headers,
                                data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_URL_FORMAT

    def test_campaign_update_with_invalid_campaign_id(self, access_token_first, campaign_valid_data):
        """
        This is a test to update a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign, self.HTTP_METHOD, self.URL,
                                                               access_token_first, campaign_valid_data)


class TestSmsCampaignWithIdHTTPDelete(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method DELETE.
    """
    URL = SmsCampaignApiUrl.CAMPAIGN
    HTTP_METHOD = 'delete'

    def test_delete_with_invalid_token(self, sms_campaign_of_user_first):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        response = requests.delete(self.URL % sms_campaign_of_user_first['id'],
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), 'It should be unauthorized (401)'

    def test_delete_campaign_in_own_domain(self, headers, user_first, sms_campaign_of_user_first):
        """
        User auth token is valid. It deletes the campaign, belong to the user, from database.
        It should get OK response.
        """
        response = requests.delete(self.URL % sms_campaign_of_user_first['id'], headers=headers)
        assert_campaign_delete(response, user_first.id, sms_campaign_of_user_first['id'])

    def test_delete_campaign_with_other_user_of_same_domain(self, headers_same, user_same_domain,
                                                            sms_campaign_of_user_first):
        """
        Some other user of same domain tries to delete the sms-campaign created by some other user.
        It should get OK response.
        """
        response = requests.delete(self.URL % sms_campaign_of_user_first['id'], headers=headers_same)
        assert_campaign_delete(response, user_same_domain.id, sms_campaign_of_user_first['id'])

    def test_with_sms_campaign_in_other_domain(self, headers, sms_campaign_in_other_domain):
        """
        User auth token is valid. It tries to delete the campaign of some other user
        from database. It should get forbidden error.
        """
        response = requests.delete(self.URL % sms_campaign_in_other_domain['id'], headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response, ForbiddenError.http_status_code())

    def test_with_deleted_campaign(self, access_token_first, sms_campaign_of_user_first):
        """
        We first delete an SMS campaign and again try to delete it. It should result in ResourceNotFound error.
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(
            sms_campaign_of_user_first, self.URL, self.URL, self.HTTP_METHOD, access_token_first)

    def test_campaign_delete_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign, self.HTTP_METHOD, self.URL,
                                                               access_token_first)
