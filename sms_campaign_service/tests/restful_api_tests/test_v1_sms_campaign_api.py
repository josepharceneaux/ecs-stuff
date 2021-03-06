"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns of SMS Campaign API.
"""
# Standard Imports
import json
from operator import itemgetter

# Third Party Imports
import requests

# Service Specific
from sms_campaign_service.tests.conftest import db
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.modules.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import (assert_campaign_delete,
                                                                 assert_campaign_creation,
                                                                 assert_valid_campaign_get, generate_campaign_data)


# Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.sms_campaign import SmsCampaign

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (InvalidUsage, InternalServerError,
                                                        ForbiddenError, ResourceNotFound)
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


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

    def test_campaigns_get_with_user_having_multiple_twilio_numbers(self, headers, user_phone_1,
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

    def test_get_with_one_campaign(self, headers, sms_campaign_of_user_first):
        """
        We have created one campaign for user. It should result in OK response and count of campaigns
        should be 1,
        """
        response = requests.get(self.URL, headers=headers)
        _assert_campaign_count_and_fields(response, sms_campaign_of_user_first, count=1)

    def test_get_all_campaigns_in_user_domain(self, headers,
                                              sms_campaign_of_user_first,
                                              sms_campaign_of_other_user_in_same_domain):
        """
        Here user gets all campaigns in its domain. It should result in OK response and count of
        campaigns should be 2 as 2 users have created campaign in one domain.
        """
        response = requests.get(self.URL, headers=headers)
        campaigns = _sort_campaigns(_assert_campaign_count_and_fields(response, count=2,
                                                                      assert_fields=False))
        sorted_campaigns = _sort_campaigns([sms_campaign_of_other_user_in_same_domain,
                                            sms_campaign_of_user_first])

        assert_valid_campaign_get(campaigns[0], sorted_campaigns[0])
        assert_valid_campaign_get(campaigns[1], sorted_campaigns[1])

    def test_get_all_campaigns_by_other_user_of_same_domain(self, headers_same,
                                                            sms_campaign_of_user_first,
                                                            sms_campaign_of_other_user_in_same_domain,
                                                            sms_campaign_with_no_candidate):
        """
        Here other user of same domain tries to get all campaigns in its domain. It should result
        in OK response and count of campaigns should be 2 as 2 user have created campaign in its domain.
        """
        response = requests.get(self.URL, headers=headers_same)
        campaigns = _sort_campaigns(_assert_campaign_count_and_fields(response, count=3,
                                                                      assert_fields=False))
        sorted_campaigns = _sort_campaigns([sms_campaign_of_other_user_in_same_domain,
                                            sms_campaign_of_user_first,
                                            sms_campaign_with_no_candidate])
        assert_valid_campaign_get(campaigns[0], sorted_campaigns[0])
        assert_valid_campaign_get(campaigns[1], sorted_campaigns[1])
        assert_valid_campaign_get(campaigns[2], sorted_campaigns[2])

    def test_get_campaigns_with_paginated_response(self, headers, bulk_sms_campaigns):
        """
        Here we test the paginated response of GET call on endpoint /v1/sms-campaigns
        """
        campaign_ids = [campaign['id'] for campaign in bulk_sms_campaigns]

        # This should get 4 campaign objects on page 1
        response = requests.get(self.URL + '?per_page=4', headers=headers)
        _assert_campaign_count_and_fields(response, bulk_sms_campaigns[0], count=4,
                                          compare_fields=False)

        for campaign in response.json()['campaigns']:
            assert campaign['id'] in campaign_ids

        # This should also get 4 campaign objects on page 2
        response = requests.get(self.URL + '?per_page=4&page=2', headers=headers)
        _assert_campaign_count_and_fields(response, bulk_sms_campaigns[0], count=4,
                                          compare_fields=False)
        for campaign in response.json()['campaigns']:
            assert campaign['id'] in campaign_ids

        # This should also get 2 campaign objects on page 3
        response = requests.get(self.URL + '?per_page=4&page=3', headers=headers)
        _assert_campaign_count_and_fields(response, bulk_sms_campaigns[0], count=2,
                                          compare_fields=False)
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
    HTTP_METHOD = 'post'
    URL = SmsCampaignApiUrl.CAMPAIGNS

    def test_campaign_creation_with_invalid_token(self):
        """
        User auth token is invalid, it should result in Unauthorized Error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL)

    def test_campaign_creation_with_invalid_header(self, access_token_first):
        """
        User auth token is valid, but content-type is not set. It should result in bad request error.
        """
        response = requests.post(self.URL, headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == InvalidUsage.http_status_code(), 'It should be a bad request (400)'

    def test_campaign_creation_with_no_user_phone_and_valid_data(self, user_first, campaign_valid_data, headers):
        """
        User has no Twilio phone number. It should result in Ok response as we will buy a Twilio
        number for user silently.
        :param campaign_valid_data: valid data to create campaign
        :param headers: valid header to POST data
        """
        response = requests.post(self.URL, headers=headers, data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, 201)
        _delete_created_number_of_user(user_first)

    def test_campaign_creation_with_no_data(self, headers, user_phone_1):
        """
        User has one mobile number, but no data was sent. It should result in bad request error.
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL, headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaign_creation_with_non_json_data(self, headers, campaign_valid_data, user_phone_1):
        """
        User has one mobile number, valid header and invalid data type (not JSON) was sent.
        It should result in bad request error.
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL, headers=headers, data=campaign_valid_data)
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaign_creation_with_missing_required_fields(self, headers, invalid_data_for_campaign_creation,
                                                            user_phone_1):
        """
        User has one phone value, valid header and invalid data (Missing required key).
        It should result in Invalid usage error.
        :param headers: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_data, missing_key = invalid_data_for_campaign_creation
        response = requests.post(self.URL, headers=headers, data=json.dumps(campaign_data))
        assert response.status_code == InvalidUsage.http_status_code(), 'It should result in bad request error'
        assert missing_key in response.json()['error']['message']

    def test_campaign_creation_with_unexpected_fields_in_data(self, campaign_valid_data, access_token_first,
                                                              user_phone_1):
        """
        User has one phone number, valid header and invalid data (unexpected fields) to
        create sms-campaign. It should result in Invalid usage error.
        """
        CampaignsTestsHelpers.test_api_with_with_unexpected_field_in_data(self.HTTP_METHOD, self.URL,
                                                                          access_token_first, campaign_valid_data)

    def test_campaign_create_with_invalid_smartlist_ids(self, access_token_first):
        """
        This is a test to create SMS campaign with invalid smartlist_ids.
        Invalid smartlist ids include Non-existing id, non-integer id, empty list, duplicate items in list etc.
        Status code should be 400 and campaign should not be created.
        """
        CampaignsTestsHelpers.campaign_create_or_update_with_invalid_smartlist(self.HTTP_METHOD, self.URL,
                                                                               access_token_first,
                                                                               generate_campaign_data())

    def test_campaign_create_with_valid_and_not_owned_smartlist_ids(self, headers, campaign_valid_data,
                                                                    smartlist_with_two_candidates_in_other_domain):
        """
        This is a test to create SMS campaign with valid smartlist id and smartlist id of some other domain.
        It should result in ForbiddenError.
        """
        data = campaign_valid_data.copy()
        data['smartlist_ids'].extend([smartlist_with_two_candidates_in_other_domain[0]])
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        CampaignsTestsHelpers.assert_non_ok_response(response, ForbiddenError.http_status_code())

    def test_campaign_create_with_invalid_campaign_name(self, access_token_first, campaign_valid_data):
        """
        This is a test to create SMS campaign with invalid campaign name. Status code should be 400 and
        campaign should not be created.
        """
        CampaignsTestsHelpers.request_with_invalid_string(self.HTTP_METHOD, self.URL,
                                                                            access_token_first,
                                                                            campaign_valid_data.copy(), 'name')

    def test_campaign_create_with_invalid_body_text(self, access_token_first, campaign_valid_data):
        """
        This is a test to create SMS campaign with invalid body_text. Status code should be 400 and
        campaign should not be created.
        """
        CampaignsTestsHelpers.request_with_invalid_string(self.HTTP_METHOD, self.URL,
                                                                            access_token_first,
                                                                            campaign_valid_data.copy(), 'body_text')

    def test_campaign_creation_with_invalid_url_in_body_text(self, campaign_valid_data, headers, user_phone_1):
        """
        User has one mobile number, valid header and invalid URL in body text(random word).
        It should result in Invalid url error, Custom error should be INVALID_URL_FORMAT.
        """
        campaign_valid_data['body_text'] += 'http://' + fake.word()
        response = requests.post(self.URL, headers=headers, data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_URL_FORMAT

    def test_campaign_creation_with_one_user_phone_and_valid_data(self, user_first, headers, campaign_valid_data,
                                                                  user_phone_1):
        """
        User has one mobile number, valid header and valid data.
        It should result in OK response (201 status code)
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(self.URL, headers=headers, data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, requests.codes.CREATED)

    def test_campaign_creation_with_one_deleted_smartlist(self, access_token_first, headers,
                                                          campaign_valid_data, user_phone_1):
        """
        We will try to create a campaign with deleted smartlist and API will raise 400 error.
        """
        smartlist_id = campaign_valid_data['smartlist_ids'][0]
        CampaignsTestsHelpers.send_request_with_deleted_smartlist(self.HTTP_METHOD, self.URL, access_token_first,
                                                                  smartlist_id, campaign_valid_data)

    def test_campaign_creation_with_other_user_of_same_domain(self, user_same_domain, headers_same,
                                                              campaign_valid_data):
        """
        Here some other user of same domain tries to create an sms-campaign.
        He should be able to create the campaign without any error.
        """
        response = requests.post(self.URL, headers=headers_same, data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_same_domain.id, requests.codes.CREATED)

    def test_campaign_creation_with_multiple_user_phone_and_valid_data(self, headers, campaign_valid_data,
                                                                       user_phone_1, user_phone_2):
        """
        User has multiple Twilio phone numbers, and valid data. It should result in internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param headers: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :param user_phone_2: user_phone fixture to assign another test phone number to user
        """
        response = requests.post(self.URL, headers=headers, data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS


class TestSmsCampaignHTTPDelete(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns and HTTP method DELETE.
    """
    HTTP_METHOD = 'delete'
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
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaigns_delete_with_no_data(self, headers):
        """
        User auth token is valid, but no data provided. It should result in bad request error.
        """
        response = requests.delete(self.URL, headers=headers)
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaigns_delete_with_non_json_data(self, headers):
        """
        User auth token is valid, but non JSON data provided. It should result in bad request error.
        """
        response = requests.delete(self.URL, headers=headers, data={'ids': [1, 2, 3]})
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, headers):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should result in bad request error.
        """
        response = requests.delete(self.URL, headers=headers, data=json.dumps({'ids': 1}))
        CampaignsTestsHelpers.assert_non_ok_response(response)

    def test_campaigns_delete_with_valid_and_not_owned_campaigns(self, headers, sms_campaign_in_other_domain,
                                                                 sms_campaign_of_user_first):
        """
        User auth token is valid, but one of the requested campaigns ids does not belong to user domain.
        It should result in Forbidden error.
        """
        response = requests.delete(self.URL, headers=headers,
                                   data=json.dumps({'ids': [sms_campaign_of_user_first['id'],
                                                            sms_campaign_in_other_domain['id']]}))
        CampaignsTestsHelpers.assert_non_ok_response(response, ForbiddenError.http_status_code())

    def test_campaigns_delete_with_valid_and_not_existing_campaigns(self, headers, sms_campaign_of_user_first):
        """
        User auth token is valid, but one of the requested campaigns ids does not exists in database.
        It should result in ResourceNotFound error.
        """
        non_existing_id = CampaignsTestsHelpers.get_non_existing_id(SmsCampaign)
        response = requests.delete(self.URL, headers=headers,
                                   data=json.dumps({'ids': [sms_campaign_of_user_first['id'], non_existing_id]}))
        CampaignsTestsHelpers.assert_non_ok_response(response, ResourceNotFound.http_status_code())

    def test_campaigns_delete_with_valid_and_invalid_campaign_ids(self, access_token_first):
        """
        User auth token is valid, but invalid data provided (ids other than int). It should result in bad request error.
        """
        CampaignsTestsHelpers.campaigns_delete_with_invalid_data(self.URL, access_token_first, SmsCampaign)

    def test_campaigns_delete_with_authorized_ids(self, headers, user_first, sms_campaign_of_user_first):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        """
        response = requests.delete(self.URL, headers=headers,
                                   data=json.dumps({'ids': [sms_campaign_of_user_first['id']]}))
        assert_campaign_delete(response, user_first.id, sms_campaign_of_user_first['id'])

    def test_delete_campaign_of_some_other_user_in_same_domain(self, headers_same,
                                                               user_same_domain, sms_campaign_of_user_first):
        """
        Here one user tries to delete campaign of some other user in same domain. Response should be OK.
        """
        response = requests.delete(self.URL, headers=headers_same,
                                   data=json.dumps({'ids': [sms_campaign_of_user_first['id']]}))
        assert_campaign_delete(response, user_same_domain.id, sms_campaign_of_user_first['id'])

    def test_campaigns_delete_with_unauthorized_id(self, headers, sms_campaign_in_other_domain):
        """
        User auth token is valid, data type is valid and ids are of those SMS campaigns that
        belong to some other user. It should result in unauthorized error.
        """
        response = requests.delete(self.URL, headers=headers,
                                   data=json.dumps({'ids': [sms_campaign_in_other_domain['id']]}))
        CampaignsTestsHelpers.assert_non_ok_response(response, ForbiddenError.http_status_code())

    def test_delete_campaigns_of_multiple_users(self, headers, user_first, sms_campaign_of_other_user_in_same_domain,
                                                sms_campaign_of_user_first):
        """
        Test with one SMS campaigns in a domain. It should result in OK response.
        """
        response = requests.delete(self.URL, headers=headers,
                                   data=json.dumps({'ids': [sms_campaign_of_other_user_in_same_domain['id'],
                                                            sms_campaign_of_user_first['id']]}))
        assert_campaign_delete(response, user_first.id, sms_campaign_of_user_first['id'])

    def test_campaigns_delete_with_deleted_record(self, headers, user_first, sms_campaign_of_user_first):
        """
        We first delete an SMS campaign, and again try to delete it. It should result in
        ResourceNotFound error.
        """
        campaign_id = sms_campaign_of_user_first['id']
        response = requests.delete(self.URL, headers=headers, data=json.dumps({'ids': [campaign_id]}))
        assert_campaign_delete(response, user_first.id, campaign_id)
        response_after_delete = requests.delete(self.URL, headers=headers, data=json.dumps({'ids': [campaign_id]}))
        CampaignsTestsHelpers.assert_non_ok_response(response_after_delete, ResourceNotFound.http_status_code())

    def test_campaigns_delete_with_unexpected_fields_in_data(self, sms_campaign_of_user_first, access_token_first,
                                                             user_phone_1):
        """
        This adds unexpected field in data to delete campaigns. It should result in Invalid usage error.
        """
        campaign_id = sms_campaign_of_user_first['id']
        CampaignsTestsHelpers.test_api_with_with_unexpected_field_in_data(self.HTTP_METHOD, self.URL,
                                                                          access_token_first, {'ids': [campaign_id]})


def _delete_created_number_of_user(user):
    # Need to commit the session here as we have saved the user_phone in another session.
    # And we do not have any user_phone for this session.
    db.session.commit()
    UserPhone.delete(user.user_phones[0])


def _assert_campaign_count_and_fields(response, referenced_campaign=None, count=0, assert_fields=True,
                                      compare_fields=True):
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


def _sort_campaigns(campaigns_list, field='id', reverse=False):
    """
    This sorts the given list of campaigns on the bases of their ids.
    :param (list) campaigns_list: List of campaigns
    :param (str) field: Name of field on which we want to sort
    :param (bool) reverse: If we want to order in reverse order, this should be True.
    """
    return sorted(campaigns_list, key=itemgetter(field), reverse=reverse)
