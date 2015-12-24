"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/sends of
    SMS Campaign API.
"""
# Standard Imports
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (ResourceNotFound, UnauthorizedError)

# Service Specific
from sms_campaign_service.tests.modules.common_functions import assert_method_not_allowed


class TestSmsCampaignSends(object):
    """
    This class contains tests for endpoint /campaigns/:id/sends
    """

    def test_for_post_request(self, auth_token, sms_campaign_of_current_user):
        """
        POST method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.post(SmsCampaignApiUrl.CAMPAIGN_SENDS_URL
                                 % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert_method_not_allowed(response, 'POST')

    def test_for_delete_request(self, auth_token, sms_campaign_of_current_user):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN_SENDS_URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_method_not_allowed(response, 'DELETE')

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should get Unauthorized error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should not be authorized (401)'

    def test_get_with_no_campaign_sent(self, auth_token, sms_campaign_of_current_user):
        """
        Here we are assuming that SMS campaign has not been sent to any of candidates,
        So no blast should be saved for the campaign. Sends count should be 0.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        _assert_counts_and_sends(response)

    def test_get_with_no_candidate_associated_to_campaign(self, auth_token,
                                                          sms_campaign_of_current_user,
                                                          create_sms_campaign_blast):
        """
        Here we are assuming that SMS campaign has been sent but no candidate was associated with
        the associated smartlists. So, sends count should be 0.

        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_blast" to create an entry in database table "sms_campaign_blast",
        and then gets the "sends" of that campaign.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :param create_sms_campaign_blast: fixture to create entry in "sms_campaign_blast" db table.
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        _assert_counts_and_sends(response)

    def test_get_with_deleted_campaign_id(self, auth_token,
                                                          sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its sends.
        It should get ResourceNotFound error.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN_URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_get = requests.get(
            SmsCampaignApiUrl.CAMPAIGN_SENDS_URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_get.status_code == ResourceNotFound.http_status_code(), \
            'Campaign should not be found (404)'

    def test_get_with_valid_token_and_two_sends(self, auth_token,
                                                         sms_campaign_of_current_user,
                                                         create_campaign_sends):
        """
        This is the case where we assume we have sent the campaign to 2 candidates. We are
        using fixtures to create campaign blast and campaign sends.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_sends" to create an entry in database table "sms_campaign_sends",
        and then gets the "sends" of that campaign. Sends count should be 2.
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.CAMPAIGN_SENDS_URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        _assert_counts_and_sends(response, count=2)


def _assert_counts_and_sends(response, count=0):
    """
    This is the common function to assert that response is returning valid 'count'
    and 'campaign_sends'
    :param response:
    :param count:
    :return:
    """
    assert response.status_code == 200, 'Response should be ok (200)'
    assert response.json()
    resp = response.json()
    assert 'count' in resp
    assert 'campaign_sends' in resp
    assert resp['count'] == count
    if not count:  # if count is 0, campaign_sends should be []
        assert not resp['campaign_sends']
    else:
        assert resp['campaign_sends']
