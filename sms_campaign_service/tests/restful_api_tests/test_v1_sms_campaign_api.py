"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns of SMS Campaign API.
"""
# Standard Imports
import json

# Third Party Imports
import requests
from werkzeug.security import gen_salt


# Service Specific
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.tests.conftest import db, CREATE_CAMPAIGN_DATA
from sms_campaign_service.modules.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import (assert_for_activity,
                                                                 assert_campaign_delete,
                                                                 assert_campaign_creation,
                                                                 assert_valid_campaign_get)
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


# Models
from sms_campaign_service.common.models.misc import Activity
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.smartlist import Smartlist
from sms_campaign_service.common.models.sms_campaign import SmsCampaign

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (InvalidUsage, InternalServerError,
                                                        ForbiddenError, ResourceNotFound)


class TestSmsCampaignHTTPGet(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns and HTTP method GET.
    """
    URL = SmsCampaignApiUrl.CAMPAIGNS

    def test_campaigns_get_with_invalid_token(self):
        """
        User auth token is invalid. It should result in Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('get', self.URL)

    def test_campaigns_get_with_no_user_twilio_number(self, headers, user_first):
        """
        User has no Twilio phone number. It should result in OK response as we will buy a number for
        user silently.
        """
        response = requests.get(self.URL, headers=headers)
        _assert_campaign_count_and_fields(response)
        _delete_created_number_of_user(user_first)

    def test_campaigns_get_with_one_user_twilio_number(self, headers, user_phone_1):
        """
        User already has a Twilio phone number. it should result in OK response. But no campaign
        has been created yet.
        """
        response = requests.get(self.URL, headers=headers)
        _assert_campaign_count_and_fields(response)

    def test_campaigns_get_with_user_having_multiple_twilio_numbers(self,
                                                                    headers,
                                                                    user_phone_1,
                                                                    user_phone_2):
        """
        User has multiple Twilio phone numbers, it should result in internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param user_phone_1: fixture to assign one test phone number to user
        :param user_phone_2: fixture to assign another test phone number to user
        """
        response = requests.get(self.URL, headers=headers)
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS

    def test_get_with_one_campaign(self, headers, sms_campaign_of_current_user):
        """
        We have created one campaign for user. It should result in OK response and count of campaigns
        should be 1,
        """
        response = requests.get(self.URL, headers=headers)
        _assert_campaign_count_and_fields(response, sms_campaign_of_current_user, count=1)

    def test_get_all_campaigns_in_user_domain(self, headers,
                                              sms_campaign_of_current_user,
                                              sms_campaign_of_other_user_in_same_domain):
        """
        Here user get all campaigns in it's domain. It should result in OK response and count of campaigns
        should be 2 as 2 user have created campaign in one domain.
        """
        response = requests.get(self.URL, headers=headers)
        campaigns = _assert_campaign_count_and_fields(response, count=2, assert_fields=False)
        assert_valid_campaign_get(campaigns[0], sms_campaign_of_current_user)
        assert_valid_campaign_get(campaigns[1], sms_campaign_of_other_user_in_same_domain)

    def test_get_all_campaigns_by_other_user_of_same_domain(self, headers_same_domain,
                                                            sms_campaign_of_current_user,
                                                            sms_campaign_of_other_user_in_same_domain,
                                                            sms_campaign_with_no_candidate):
        """
        Here other user of same domain tries to get all campaign in its domain. It should result
        in OK response and count of campaign should be 2 as 2 user have created campaign in its domain.
        """
        response = requests.get(self.URL, headers=headers_same_domain)
        campaigns = _assert_campaign_count_and_fields(response, count=3, assert_fields=False)
        assert_valid_campaign_get(campaigns[0], sms_campaign_of_other_user_in_same_domain)
        assert_valid_campaign_get(campaigns[1], sms_campaign_of_current_user)
        assert_valid_campaign_get(campaigns[2], sms_campaign_with_no_candidate)

    def test_get_campaigns_with_paginated_response(self, headers, bulk_sms_campaigns):
        """
        Here we test the paginated response of GET call on endpoint /v1/sms-campaigns
        """
        campaign_ids = [campaign['id'] for campaign in bulk_sms_campaigns]

        # This should get 4 campaign objects on page 1
        response = requests.get(self.URL + '?per_page=4', headers=headers)
        _assert_campaign_count_and_fields(response, bulk_sms_campaigns[0], count=4, compare_fields=False)

        for campaign in response.json()['campaigns']:
            assert campaign['id'] in campaign_ids

        # This should also get 4 campaign objects on page 2
        response = requests.get(self.URL + '?per_page=4&page=2', headers=headers)
        _assert_campaign_count_and_fields(response, bulk_sms_campaigns[0], count=4, compare_fields=False)
        for campaign in response.json()['campaigns']:
            assert campaign['id'] in campaign_ids

        # This should also get 2 campaign objects on page 3
        response = requests.get(self.URL + '?per_page=4&page=3', headers=headers)
        _assert_campaign_count_and_fields(response, bulk_sms_campaigns[0], count=2, compare_fields=False)
        for campaign in response.json()['campaigns']:
            assert campaign['id'] in campaign_ids

        # This should not campaign objects as total campaigns are 10 and we are trying
        # to access 4th page with per_page=4.
        response = requests.get(self.URL + '?per_page=4&page=4', headers=headers)
        _assert_campaign_count_and_fields(response, count=0)


class TestSmsCampaignHTTPPost(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns and HTTP method POST.
    """
    URL = SmsCampaignApiUrl.CAMPAIGNS

    def test_campaign_creation_with_invalid_token(self):
        """
        User auth token is invalid, it should result in Unauthorized Error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('post', self.URL)

    def test_campaign_creation_with_invalid_header(self, access_token_first):
        """
        User auth token is valid, but content-type is not set. It should result in bad request error.
        """
        response = requests.post(self.URL,
                                 headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'
        assert 'header' in response.json()['error']['message']

    def test_campaign_creation_with_no_user_phone_and_valid_data(self, user_first,
                                                                 campaign_valid_data,
                                                                 headers):
        """
        User has no Twilio phone number. It should result in Ok response as we will buy a Twilio
        number for user silently.
        :param campaign_valid_data: valid data to create campaign
        :param headers: valid header to POST data
        """
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, 201)
        _delete_created_number_of_user(user_first)

    def test_campaign_creation_with_no_data(self,
                                            headers,
                                            user_phone_1):
        """
        User has one phone value, but no data was sent. It should result in bad request error.
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL,
                                 headers=headers)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_non_json_data(self, headers,
                                                  campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and invalid data type (not JSON) was sent.
        It should result in bad request error.
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=campaign_valid_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_missing_body_text_in_data(self, campaign_data_unknown_key_text,
                                                              headers, user_phone_1):
        """
        User has one phone value, valid header and invalid data (unknown key "text") was sent.
        It should result in Invalid usage error.
        :param campaign_data_unknown_key_text: Invalid data to create SMS campaign.
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_data_unknown_key_text))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should result in bad request error'

    def test_campaign_creation_with_missing_smartlist_ids_in_data(
            self, headers, user_phone_1):
        """
        User has one phone value, valid header and invalid data (Missing key "smartlist_ids").
        It should result in Invalid usage error.
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_data = CREATE_CAMPAIGN_DATA.copy()
        del campaign_data['smartlist_ids']
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_data))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should result in bad request error'

    def test_campaign_creation_with_one_user_phone_and_unknown_smartlist_ids(
            self, campaign_valid_data, headers, user_phone_1):
        """
        User has one phone value, valid header and invalid data (Unknown "smartlist_ids").
        It should result in InvalidUsage error,
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_valid_data['smartlist_ids'] = [gen_salt(2)]
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_creation_with_invalid_url_in_body_text(self, campaign_valid_data,
                                                             headers, user_phone_1):
        """
        User has one phone value, valid header and invalid URL in body text(random word).
        It should result in Invalid url error, Custom error should be INVALID_URL_FORMAT.
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_valid_data['body_text'] += 'http://' + fake.word()
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_URL_FORMAT

    def test_campaign_creation_with_one_user_phone_and_one_unknown_smartlist(
            self, user_first, headers, campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and valid data. One of the Smartlist ids being sent
        to the server doesn't actually exist in the getTalent's database.
        It should result in OK response (207 status code) as code should create campaign for valid
        smartlist ids.
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_valid_data['smartlist_ids'].append(gen_salt(2))
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, 207)

    def test_campaign_creation_with_one_user_phone_and_valid_data(self,
                                                                  user_first,
                                                                  headers,
                                                                  campaign_valid_data,
                                                                  user_phone_1):
        """
        User has one phone value, valid header and valid data.
        It should result in OK response (201 status code)
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, requests.codes.CREATED)

    def test_campaign_creation_with_other_user_of_same_domain(self, user_same_domain,
                                                              headers_same_domain,
                                                              campaign_valid_data):
        """
        Here some other user of same domain tries to create an sms-campaign.
        He should be able to create the campaign without any error.
        """
        response = requests.post(self.URL,
                                 headers=headers_same_domain,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_same_domain.id, requests.codes.CREATED)

    def test_campaign_creation_with_multiple_user_phone_and_valid_data(self,
                                                                       headers,
                                                                       campaign_valid_data,
                                                                       user_phone_1,
                                                                       user_phone_2):
        """
        User has multiple Twilio phone numbers, and valid data. It should result in internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :param user_phone_2: user_phone fixture to assign another test phone number to user
        """
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS

    def test_campaign_create_with_valid_and_non_existing_and_not_owned_smartlist_ids(
            self, headers, user_first, campaign_valid_data,
            smartlist_with_two_candidates_in_other_domain):
        """
        This is a test to create SMS campaign with valid and invalid smartlist_ids.
        Status code should be 207 and campaign should be created.
        """
        data = campaign_valid_data.copy()
        last_id = CampaignsTestsHelpers.get_last_id(Smartlist)
        data['smartlist_ids'].extend([last_id, 0, smartlist_with_two_candidates_in_other_domain[0]])
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(data))
        assert_campaign_creation(response, user_first.id, 207)

    def test_campaign_create_with_invalid_smartlist_ids(self, headers,
                                                        campaign_valid_data,
                                                        smartlist_with_two_candidates_in_other_domain):
        """
        This is a test to create SMS campaign with invalid smartlist_ids.
        Status code should be 400 and campaign should not be created.
        """
        data = campaign_valid_data.copy()
        non_existing_id = CampaignsTestsHelpers.get_non_existing_id(Smartlist)
        data['smartlist_ids'] = [non_existing_id, 0, smartlist_with_two_candidates_in_other_domain[0]]
        response = requests.post(self.URL,
                                 headers=headers,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()


class TestSmsCampaignHTTPDelete(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns and HTTP method DELETE.
    """

    URL = SmsCampaignApiUrl.CAMPAIGNS

    def test_campaigns_delete_with_invalid_token(self):
        """
        User auth token is invalid, it should result in Unauthorized.
        """
        CampaignsTestsHelpers.request_with_invalid_token('delete', self.URL)

    def test_campaigns_delete_with_invalid_header(self, headers):
        """
        User auth token is valid, but no content-type provided in header.
        It should result in bad request error.
        """
        response = requests.delete(self.URL, headers=headers)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_no_data(self, headers):
        """
        User auth token is valid, but no data provided. It should result in bad request error.
        """
        response = requests.delete(self.URL, headers=headers)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_non_json_data(self, headers):
        """
        User auth token is valid, but non JSON data provided. It should result in bad request error.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data={
                                       'ids': [1, 2, 3]
                                   })
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, headers):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should result in bad request error.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': 1
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_invalid_and_not_owned_and_non_existing_ids(
            self, headers, sms_campaign_in_other_domain):
        """
        User auth token is valid, but invalid data provided
        (ids other than int, not owned campaign and Non-exisiting),
        It should result in bad request error.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [0, 'a', 'b', sms_campaign_in_other_domain['id']]
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_authorized_ids(self, headers, user_first,
                                                  sms_campaign_of_current_user):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user['id']]
                                   }))
        assert_campaign_delete(response, user_first.id, sms_campaign_of_current_user['id'])

    def test_delete_campaign_of_some_other_user_in_same_domain(self, headers_same_domain,
                                                               user_same_domain,
                                                               sms_campaign_of_current_user):
        """
        Here one user tries to delete campaign of some other user in same domain.
        Response should be OK.
        """
        response = requests.delete(self.URL,
                                   headers=headers_same_domain,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user['id']]
                                   }))
        assert_campaign_delete(response, user_same_domain.id, sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_unauthorized_id(self, headers,
                                                   sms_campaign_in_other_domain):
        """
        User auth token is valid, data type is valid and ids are of those SMS campaigns that
        belong to some other user. It should result in unauthorized error.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [sms_campaign_in_other_domain['id']]
                                   }))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should result in forbidden error (403)'

    def test_delete_campaigns_of_multiple_users(self, headers, user_first,
                                                sms_campaign_of_other_user_in_same_domain,
                                                sms_campaign_of_current_user):
        """
        Test with one authorized and one unauthorized SMS campaign. It should result in 207
        status code.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user_in_same_domain['id'],
                                               sms_campaign_of_current_user['id']]
                                   }))
        assert_campaign_delete(response, user_first.id, sms_campaign_of_current_user['id'])

    def test_campaigns_delete_authorized_and_unauthorized_ids(self, headers, user_first,
                                                              sms_campaign_in_other_domain,
                                                              sms_campaign_of_current_user):
        """
        Test with one authorized and one unauthorized SMS campaign. It should result in 207
        status code.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [sms_campaign_in_other_domain['id'],
                                               sms_campaign_of_current_user['id']]
                                   }))
        assert response.status_code == 207
        assert sms_campaign_in_other_domain['id'] in response.json()['not_owned_ids']
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_DELETE,
                            sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_existing_and_non_existing_ids(self, headers, user_first,
                                                                 sms_campaign_of_current_user):
        """
        Test with one existing, and one non existing ids of SMS campaign.
        It should result in 207 status code.
        """
        non_existing_id = CampaignsTestsHelpers.get_non_existing_id(SmsCampaign)
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [non_existing_id, sms_campaign_of_current_user['id']]
                                   }))
        assert response.status_code == 207
        assert non_existing_id in response.json()['not_found_ids']
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_DELETE,
                            sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_valid_and_invalid_ids(self, headers, user_first,
                                                         sms_campaign_of_current_user):
        """
        Test with one valid, and one invalid id of SMS campaign.
        It should result in 207 status code.
        """
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [0, sms_campaign_of_current_user['id']]
                                   }))
        assert response.status_code == 207
        assert 0 in response.json()['not_deleted_ids']
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_DELETE,
                            sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_deleted_record(self, headers, user_first,
                                                  sms_campaign_of_current_user):
        """
        We first delete an SMS campaign, and again try to delete it. It should result in
        ResourceNotFound error.
        """
        campaign_id = sms_campaign_of_current_user['id']
        response = requests.delete(self.URL,
                                   headers=headers,
                                   data=json.dumps({
                                       'ids': [campaign_id]
                                   }))
        assert_campaign_delete(response, user_first.id, campaign_id)
        response_after_delete = requests.delete(self.URL,
                                                headers=headers,
                                                data=json.dumps({
                                                    'ids': [campaign_id]
                                                }))
        assert response_after_delete.status_code == ResourceNotFound.http_status_code()


def _delete_created_number_of_user(user):
    # Need to commit the session here as we have saved the user_phone in another session.
    # And we do not have any user_phone for this session.
    db.session.commit()
    UserPhone.delete(user.user_phones[0])


def _assert_campaign_count_and_fields(response, referenced_campaign=None, count=0,
                                      assert_fields=True, compare_fields=True):
    """
    This function is used to asserts that we get expected number of SMS campaigns.
    It then asserts that the campaign object has all the fields that we are expecting
    """
    assert response.status_code == requests.codes.OK, 'Status should be Ok (200)'
    assert response.json()
    resp = response.json()
    assert 'campaigns' in resp
    assert len(resp['campaigns']) == count
    if assert_fields:
        for campaign in resp['campaigns']:
            assert_valid_campaign_get(campaign, referenced_campaign, compare_fields=compare_fields)
    return resp['campaigns']
