"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /campaigns/:id/sms_campaign_sends of SMS Campaign API.
"""
# Standard Imports
import requests

# Application Specific
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (MethodNotAllowed, ResourceNotFound,
                                                        UnauthorizedError)


class TestSmsCampaignSends:
    """
    This class contains tests for endpoint /campaigns/:id/sms_campaign_sends
    """

    def test_for_post_request(self, auth_token, sms_campaign_of_current_user):
        """
        POST method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == MethodNotAllowed.http_status_code(), \
            'POST method should not be allowed (405)'

    def test_for_delete_request(self, auth_token, sms_campaign_of_current_user):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == MethodNotAllowed.http_status_code(),\
            'DELETE method should not be allowed (405)'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should get Unauthorized error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should not be authorized (401)'

    def test_get_with_valid_token_and_no_blasts_saved(self, auth_token,
                                                      sms_campaign_of_current_user):
        """
        SMS campaign is not sent to any of candidates, so there will be no
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Response should be ok (200)'
        assert 'count' in response.json()
        assert response.json()['count'] == 0
        assert 'campaign_sends' in response.json()
        assert response.json()['campaign_sends'] == []

    def test_get_with_valid_token_and_with_campaign_blast(self, auth_token,
                                                          sms_campaign_of_current_user,
                                                          create_sms_campaign_blast):
        """
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_blast" to create an entry in database table "sms_campaign_blast",
        and then gets the "sends" of that campaign.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :param create_sms_campaign_blast: fixture to create entry in "sms_campaign_blast" db table.
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Response should be ok (200)'
        assert 'count' in response.json()
        assert response.json()['count'] == 0
        assert 'campaign_sends' in response.json()
        assert response.json()['campaign_sends'] == []

    def test_get_with_valid_token_and_deleted_campaign_id(self, auth_token,
                                                          sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its sends.
        It should get not found error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_get = requests.get(
            SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_get.status_code == ResourceNotFound.http_status_code(), \
            'Campaign should not be found (404)'

    def test_get_with_valid_token_and_two_campaign_sends(self, auth_token,
                                                         sms_campaign_of_current_user,
                                                         create_campaign_sends):
        """
        It first deletes a campaign from database and try to get its sends.
        It should get not found error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Response should be ok (200)'
        assert 'count' in response.json()
        assert response.json()['count'] == 2
        assert 'campaign_sends' in response.json()
