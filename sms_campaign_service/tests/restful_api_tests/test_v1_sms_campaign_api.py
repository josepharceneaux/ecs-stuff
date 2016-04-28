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
                                                                 assert_campaign_creation)
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


# Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import Activity
from sms_campaign_service.common.models.smartlist import Smartlist
from sms_campaign_service.common.models.sms_campaign import SmsCampaign

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (UnauthorizedError, InvalidUsage,
                                                        InternalServerError, ForbiddenError,
                                                        ResourceNotFound)


class TestSmsCampaignHTTPGet(object):
    """
    This class contains tests for endpoint /campaigns/ and HTTP method GET.
    """

    def test_campaigns_get_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaigns_get_with_no_user_twilio_number(self, access_token_first, user_first):
        """
        User has no Twilio phone number. It should get OK response as we will buy a number for
        user silently.
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        _assert_counts_and_campaigns(response)
        _delete_created_number_of_user(user_first)

    def test_campaigns_get_with_one_user_twilio_number(self, access_token_first,
                                                       user_phone_1):
        """
        User already has a Twilio phone number. it should get OK response. But no campaign
        has been created yet.
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        _assert_counts_and_campaigns(response)

    def test_campaigns_get_with_user_having_multiple_twilio_numbers(self,
                                                                    access_token_first,
                                                                    user_phone_1,
                                                                    user_phone_2):
        """
        User has multiple Twilio phone numbers, it should get internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param access_token_first: access token of user
        :param user_phone_1: fixture to assign one test phone number to user
        :param user_phone_2: fixture to assign another test phone number to user
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS

    def test_get_with_one_campaign(self, access_token_first, sms_campaign_of_current_user):
        """
        We have created one campaign for user. It should get OK response and count of campaigns
        should be 1,
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGNS,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        _assert_counts_and_campaigns(response, count=1)


class TestSmsCampaignHTTPPost(object):
    """
    This class contains tests for endpoint /campaigns/ and HTTP method POST.
    """

    def test_campaign_creation_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaign_creation_with_invalid_header(self, access_token_first):
        """
        User auth token is valid, but content-type is not set.
        it should get bad request error.
        :param access_token_first: access token of current user
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaign_creation_with_no_user_phone_and_valid_data(self, user_first,
                                                                 campaign_valid_data,
                                                                 valid_header):
        """
        User has no Twilio phone number. It should get Ok response as we will buy a Twilio
        number for user silently.
        :param campaign_valid_data: valid data to create campaign
        :param valid_header: valid header to POST data
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, 201)
        _delete_created_number_of_user(user_first)

    def test_campaign_creation_with_no_data(self,
                                            valid_header,
                                            user_phone_1):
        """
        User has one phone value, but no data was sent. It should get bad request error.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_non_json_data(self, valid_header,
                                                  campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and invalid data type (not JSON) was sent.
        It should get bad request error.
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=campaign_valid_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_campaign_creation_with_missing_body_text_in_data(self, campaign_data_unknown_key_text,
                                                              valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (unknown key "text") was sent.
        It should get Invalid usage error.
        :param campaign_data_unknown_key_text: Invalid data to create SMS campaign.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_data_unknown_key_text))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should get bad request error'

    def test_campaign_creation_with_missing_smartlist_ids_in_data(
            self, valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (Missing key "smartlist_ids").
        It should get Invalid usage error.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_data = CREATE_CAMPAIGN_DATA.copy()
        del campaign_data['smartlist_ids']
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_data))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should get bad request error'

    def test_campaign_creation_with_one_user_phone_and_unknown_smartlist_ids(
            self, campaign_valid_data, valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid data (Unknown "smartlist_ids").
        It should get InvalidUsage error,
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_valid_data['smartlist_ids'] = [gen_salt(2)]
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_creation_with_invalid_url_in_body_text(self, campaign_valid_data,
                                                             valid_header, user_phone_1):
        """
        User has one phone value, valid header and invalid URL in body text(random word).
        It should get Invalid url error, Custom error should be INVALID_URL_FORMAT.
        :param valid_header: valid header to POST data
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_valid_data['body_text'] += 'http://' + fake.word()
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_URL_FORMAT

    def test_campaign_creation_with_one_user_phone_and_one_unknown_smartlist(
            self, user_first, valid_header, campaign_valid_data, user_phone_1):
        """
        User has one phone value, valid header and valid data. One of the Smartlist ids being sent
        to the server doesn't actually exist in the getTalent's database.
        It should get OK response (207 status code) as code should create campaign for valid
        smartlist ids.
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        campaign_valid_data['smartlist_ids'].append(gen_salt(2))
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, 207)

    def test_campaign_creation_with_one_user_phone_and_valid_data(self,
                                                                  user_first,
                                                                  valid_header,
                                                                  campaign_valid_data,
                                                                  user_phone_1):
        """
        User has one phone value, valid header and valid data.
        It should get OK response (201 status code)
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert_campaign_creation(response, user_first.id, 201)

    def test_campaign_creation_with_multiple_user_phone_and_valid_data(self,
                                                                       valid_header,
                                                                       campaign_valid_data,
                                                                       user_phone_1,
                                                                       user_phone_2):
        """
        User has multiple Twilio phone numbers, and valid data. It should get internal server error.
        Error code should be 5002 (MultipleTwilioNumbersFoundForUser)
        :param valid_header: valid header to POST data
        :param campaign_valid_data: valid data to create SMS campaign
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :param user_phone_2: user_phone fixture to assign another test phone number to user
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == InternalServerError.http_status_code(), \
            'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == SmsCampaignApiException.MULTIPLE_TWILIO_NUMBERS

    def test_campaign_create_with_valid_and_non_existing_and_not_owned_smartlist_ids(
            self, valid_header, user_first, campaign_valid_data,
            smartlist_with_two_candidates_in_other_domain):
        """
        This is a test to create SMS campaign with valid and invalid smartlist_ids.
        Status code should be 207 and campaign should be created.
        """
        data = campaign_valid_data.copy()
        last_id = CampaignsTestsHelpers.get_last_id(Smartlist)
        data['smartlist_ids'].extend([last_id, 0, smartlist_with_two_candidates_in_other_domain[0]])
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert_campaign_creation(response, user_first.id, 207)

    def test_campaign_create_with_invalid_smartlist_ids(self, valid_header,
                                                        campaign_valid_data,
                                                        smartlist_with_two_candidates_in_other_domain):
        """
        This is a test to create SMS campaign with invalid smartlist_ids.
        Status code should be 400 and campaign should not be created.
        """
        data = campaign_valid_data.copy()
        last_id = CampaignsTestsHelpers.get_last_id(Smartlist)
        data['smartlist_ids'] = [last_id + 100, 0, smartlist_with_two_candidates_in_other_domain[0]]
        response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                                 headers=valid_header,
                                 data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()


class TestSmsCampaignHTTPDelete(object):
    """
    This class contains tests for endpoint /campaigns/ and HTTP method DELETE.
    """

    def test_campaigns_delete_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_campaigns_delete_with_invalid_header(self, access_token_first):
        """
        User auth token is valid, but no content-type provided in header.
        It should get bad request error.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_no_data(self, valid_header):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS, headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_non_json_data(self, valid_header):
        """
        User auth token is valid, but non JSON data provided. It should get bad request error.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data={
                                       'ids': [1, 2, 3]
                                   })
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_campaign_ids_in_non_list_form(self, valid_header):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should get bad request error.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': 1
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_invalid_and_not_owned_and_non_existing_ids(
            self, valid_header, sms_campaign_in_other_domain):
        """
        User auth token is valid, but invalid data provided
        (ids other than int, not owned campaign and Non-exisiting),
        It should get bad request error.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [0, 'a', 'b', sms_campaign_in_other_domain['id']]
                                   }))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_campaigns_delete_with_authorized_ids(self, valid_header, user_first,
                                                  sms_campaign_of_current_user):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be OK.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user['id']]
                                   }))
        assert_campaign_delete(response, user_first.id, sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_unauthorized_id(self, valid_header,
                                                   sms_campaign_in_other_domain):
        """
        User auth token is valid, data type is valid and ids are of those SMS campaigns that
        belong to some other user. It should get unauthorized error.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_in_other_domain['id']]
                                   }))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'

    def test_delete_campaigns_of_multiple_users(self, valid_header, user_first,
                                                sms_campaign_of_other_user_in_same_domain,
                                                sms_campaign_of_current_user):
        """
        Test with one authorized and one unauthorized SMS campaign. It should get 207
        status code.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user_in_same_domain.id,
                                               sms_campaign_of_current_user['id']]
                                   }))
        assert_campaign_delete(response, user_first.id, sms_campaign_of_current_user['id'])

    def test_campaigns_delete_authorized_and_unauthorized_ids(self, valid_header, user_first,
                                                              sms_campaign_in_other_domain,
                                                              sms_campaign_of_current_user):
        """
        Test with one authorized and one unauthorized SMS campaign. It should get 207
        status code.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [sms_campaign_in_other_domain['id'],
                                               sms_campaign_of_current_user['id']]
                                   }))
        assert response.status_code == 207
        assert sms_campaign_in_other_domain['id'] in response.json()['not_owned_ids']
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_DELETE,
                            sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_existing_and_non_existing_ids(self, valid_header, user_first,
                                                                 sms_campaign_of_current_user):
        """
        Test with one existing, and one non existing ids of SMS campaign.
        It should get 207 status code.
        """
        non_existing_id = CampaignsTestsHelpers.get_last_id(SmsCampaign) + 1000
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [non_existing_id, sms_campaign_of_current_user['id']]
                                   }))
        assert response.status_code == 207
        assert non_existing_id in response.json()['not_found_ids']
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_DELETE,
                            sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_valid_and_invalid_ids(self, valid_header, user_first,
                                                         sms_campaign_of_current_user):
        """
        Test with one valid, and one invalid id of SMS campaign.
        It should get 207 status code.
        """
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [0, sms_campaign_of_current_user['id']]
                                   }))
        assert response.status_code == 207
        assert 0 in response.json()['not_deleted_ids']
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_DELETE,
                            sms_campaign_of_current_user['id'])

    def test_campaigns_delete_with_deleted_record(self, valid_header, user_first,
                                                  sms_campaign_of_current_user):
        """
        We first delete an SMS campaign, and again try to delete it. It should get
        ResourceNotFound error.
        """
        campaign_id = sms_campaign_of_current_user['id']
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                   headers=valid_header,
                                   data=json.dumps({
                                       'ids': [campaign_id]
                                   }))
        assert_campaign_delete(response, user_first.id, campaign_id)
        response_after_delete = requests.delete(SmsCampaignApiUrl.CAMPAIGNS,
                                                headers=valid_header,
                                                data=json.dumps({
                                                    'ids': [campaign_id]
                                                }))
        assert response_after_delete.status_code == ResourceNotFound.http_status_code()


def _assert_counts_and_campaigns(response, count=0):
    """
    This function is used to asserts that we ger expected number of SMS campaigns
    """
    assert response.status_code == requests.codes.OK, 'Status should be Ok (200)'
    assert response.json()
    resp = response.json()
    assert 'campaigns' in resp
    assert len(resp['campaigns']) == count


def _delete_created_number_of_user(user):
    # Need to commit the session here as we have saved the user_phone in another session.
    # And we do not have any user_phone for this session.
    db.session.commit()
    UserPhone.delete(user.user_phones[0])
