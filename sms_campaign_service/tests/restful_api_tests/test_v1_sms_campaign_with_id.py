"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id of SMS Campaign API.
"""
# Standard Imports
import json

# Third Party
import requests

# Service Specific
from sms_campaign_service.common.utils.handy_functions import to_utc_str
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.modules.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import assert_campaign_delete

# Common Utils
from sms_campaign_service.common.models.misc import Frequency
from sms_campaign_service.common.tests.sample_data import fake
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.smartlist import Smartlist
from sms_campaign_service.common.datetime_utils import utc_isoformat
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.error_handling import (UnauthorizedError, ResourceNotFound,
                                                        ForbiddenError,
                                                        InvalidUsage)
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestSmsCampaignWithIdHTTPGET(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method GET.

    """
    HTTP_METHOD = 'get'
    URL = SmsCampaignApiUrl.CAMPAIGN

    def test_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_get_campaign_in_same_domain(self, access_token_first, sms_campaign_of_current_user):
        """
        User auth token is valid. It uses 'sms_campaign_of_current_user' fixture
        to create an SMS campaign in database. It gets that record from GET HTTP request
        Response should be OK. It then assert all fields of record got from GET call with the
        original field values(provided at time of creation of campaign).
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 200, 'Response should be ok (200)'
        # verify all the field values
        campaign = sms_campaign_of_current_user
        response_campaign = response.json()['campaign']
        assert response_campaign['name'] == campaign.name
        assert response_campaign['body_text'] == campaign.body_text
        assert response_campaign['list_ids'] == [smartlist.id for smartlist
                                                 in sms_campaign_of_current_user.smartlists]

    def test_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain):
        """
        User auth token is valid. It uses 'sms_campaign_in_other_domain' fixture
        to create an SMS campaign in database. It gets that record from GET HTTP request
        Response should get Forbidden error campaign does not belong to domain of logged-in user.
        :return:
        """
        response = requests.get(self.URL % sms_campaign_in_other_domain.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error(403)'

    def test_with_id_of_deleted_record(self, access_token_first,
                                       sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign and then GETs the record from db.
        It should get ResourceNotFound error.
        :return:
        """
        response = requests.delete(self.URL % sms_campaign_of_current_user.id,
                                   headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 200, 'should get ok response (200)'
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == ResourceNotFound.http_status_code(), \
            'Record should not be found (404)'

    def test_get_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get campaign object which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)


class TestSmsCampaignWithIdHTTPPUT(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method POST.
    """
    HTTP_METHOD = 'put'
    URL = SmsCampaignApiUrl.CAMPAIGN

    def test_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_with_invalid_header(self, access_token_first, sms_campaign_of_current_user):
        """
        User auth token is valid, but content-type is not set.
        it should get bad request error.
        :param access_token_first: access token of current user
        :return:
        """
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be a bad request (400)'

    def test_updating_owned_campaign(self, valid_header,
                                     campaign_valid_data,
                                     sms_campaign_of_current_user):
        """
        This uses fixture to create an sms_campaign record in db. It then makes a POST
        call to update that record with name modification. If status code is 200, it then
        gets the record from database and assert the 'name' of modified record.
        :return:
        """
        data = campaign_valid_data.copy()
        modified_name = 'Modified Name'
        data.update({'name': modified_name})
        scheduler_data = generate_campaign_schedule_data()
        data.update(generate_campaign_schedule_data())
        response_post = requests.put(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
            headers=valid_header,
            data=json.dumps(data))
        assert response_post.status_code == 200, 'Response should be ok (200)'

        # get updated record to verify the change we made in name
        response_get = requests.get(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id, headers=valid_header)
        assert response_get.status_code == 200, 'Response should be ok (200)'
        resp = response_get.json()['campaign']
        assert resp
        assert resp['name'] == modified_name
        assert resp['frequency'].lower() in Frequency.standard_frequencies()
        # TODO: Need to update datetime format for SMS campaign API.
        # assert resp['start_datetime'] == scheduler_data['start_datetime']
        # assert resp['end_datetime'] == scheduler_data['end_datetime']

    def test_updating_not_owned_sms_campaign(self, valid_header, sms_campaign_in_other_domain,
                                             campaign_valid_data, user_phone_1):
        """
        Here we try to update a campaign which does not belong to domain of logged-in user.
        It should get forbidden error.
        """
        modified_name = 'Modified Name'
        campaign_valid_data.update({'name': modified_name})
        response_post = requests.put(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_in_other_domain.id,
            headers=valid_header,
            data=json.dumps(campaign_valid_data))
        assert response_post.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'

    def test_updating_deleted_record(self, valid_header, user_first,
                                     sms_campaign_of_current_user,
                                     campaign_valid_data):
        """
        User auth token is valid. It deletes the campaign from database and then tries
        to update the record. It should get ResourceNotFound error.
        :return:
        """
        campaign_id = sms_campaign_of_current_user.id
        response_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id, headers=valid_header)
        assert_campaign_delete(response_delete, user_first.id, campaign_id)
        response_post = requests.put(SmsCampaignApiUrl.CAMPAIGN % campaign_id,
                                     headers=valid_header,
                                     data=json.dumps(campaign_valid_data))
        assert response_post.status_code == ResourceNotFound.http_status_code(), \
            'Record should not be found (404)'

    def test_with_no_data(self, valid_header,
                          sms_campaign_of_current_user):
        """
        User auth token is valid but no data is provided. It should get bad request error.
        :return:
        """
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=valid_header)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should get bad request error (400)'

    def test_with_non_json_data(self, valid_header, campaign_valid_data,
                                sms_campaign_of_current_user):
        """
        This tries to update SMS campaign record (in sms_campaign table) providing data in dict
        format rather than JSON. It should get bad request error.
        """
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=valid_header,
                                data=campaign_valid_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'Should be a bad request (400)'

    def test_with_missing_body_text_in_data(self, valid_header,
                                            campaign_data_unknown_key_text,
                                            sms_campaign_of_current_user):
        """
        It tries to update the already present sms_campaign record with invalid_data.
        campaign_data_unknown_key_text (fixture) has no 'body_text' (which is mandatory) field
        It should get bad request error.
        :param campaign_data_unknown_key_text: fixture to get invalid data to update old record
        :param sms_campaign_of_current_user: fixture to create sms_campaign record in database
                                            fo current user.
        :return:
        """
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=valid_header,
                                data=json.dumps(campaign_data_unknown_key_text))
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should get bad request error'

    def test_campaign_update_with_invalid_url_in_body_text(self, campaign_valid_data,
                                                           valid_header,
                                                           sms_campaign_of_current_user):
        """
        User has one phone value, valid header and invalid URL in body text(random word).
        It should get invalid usage error, Custom error should be INVALID_URL_FORMAT.
        :param valid_header: valid header to POST data
        :return:
        """
        campaign_valid_data['body_text'] += 'http://' + fake.word()
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=valid_header,
                                data=json.dumps(campaign_valid_data))
        assert response.status_code == InvalidUsage.http_status_code()
        assert response.json()['error']['code'] == SmsCampaignApiException.INVALID_URL_FORMAT

    def test_campaign_update_with_valid_and_invalid_smartlist_ids(self, valid_header,
                                                                  campaign_valid_data,
                                                                  smartlist_of_other_domain,
                                                                  sms_campaign_of_current_user):
        """
        This is a test to update a campaign which does not exists in database.
        :return:
        """
        data = campaign_valid_data.copy()
        last_id = CampaignsTestsHelpers.get_last_id(Smartlist)
        data['smartlist_ids'].extend([last_id, 0, smartlist_of_other_domain.id])
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=valid_header,
                                data=json.dumps(data))
        assert response.status_code == 207

    def test_campaign_update_with_invalid_smartlist_ids(self, valid_header,
                                                        campaign_valid_data,
                                                        smartlist_of_other_domain,
                                                        sms_campaign_of_current_user):
        """
        This is a test to update a campaign which does not exists in database.
        :return:
        """
        data = campaign_valid_data.copy()
        last_id = CampaignsTestsHelpers.get_last_id(Smartlist)
        data['smartlist_ids'] = [last_id + 100, 0, smartlist_of_other_domain.id]
        response = requests.put(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
                                headers=valid_header,
                                data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_campaign_update_with_invalid_campaign_id(self, access_token_first,
                                                      campaign_valid_data):
        """
        This is a test to update a campaign which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               campaign_valid_data)


class TestSmsCampaignWithIdHTTPDelete(object):
    """
    This class contains tests for endpoint /campaigns/:id and HTTP method DELETE.
    """
    URL = SmsCampaignApiUrl.CAMPAIGN
    HTTP_METHOD = 'delete'

    def test_delete_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.delete(self.URL % sms_campaign_of_current_user.id,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_owned_sms_campaign(self, valid_header, user_first, sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign, belong to the user, from database.
        It should get OK response.
        :return:
        """
        response = requests.delete(self.URL % sms_campaign_of_current_user.id,
                                   headers=valid_header)
        assert_campaign_delete(response, user_first.id, sms_campaign_of_current_user.id)

    def test_not_owned_sms_campaign(self, valid_header, sms_campaign_in_other_domain):
        """
        User auth token is valid. It tries to delete the campaign of some other user
        from database. It should get forbidden error.
        :return:
        """
        response = requests.delete(self.URL % sms_campaign_in_other_domain.id,
                                   headers=valid_header)
        assert response.status_code == ForbiddenError.http_status_code(), \
            'it should get forbidden error (403)'

    def test_with_deleted_campaign(self, valid_header, user_first, sms_campaign_of_current_user):
        """
        We first delete an SMS campaign, and again try to delete it. It should get
        ResourceNotFound error.
        :return:
        """
        campaign_id = sms_campaign_of_current_user.id
        response = requests.delete(self.URL % campaign_id, headers=valid_header)
        assert_campaign_delete(response, user_first.id, campaign_id)
        response_after_delete = requests.delete(self.URL % campaign_id, headers=valid_header)
        assert response_after_delete.status_code == ResourceNotFound.http_status_code()

    def test_campaign_delete_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)
