"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /campaigns/:id/send of SMS Campaign API.
"""
# Standard Imports
import requests

# Application Specific
from sms_campaign_service.tests.conftest import SMS_CAMPAIGN_PROCESS_SEND_URL, \
    SMS_CAMPAIGN_WITH_ID_URL


class TestSendSmsCampaign:
    """
    This class contains tests for endpoint /campaigns/:id/send
    """

    def test_for_get_request(self, auth_token, sms_campaign_of_current_user):
        """
        POST method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 405, 'POST method should not be allowed (405)'

    def test_for_delete_request(self, auth_token, sms_campaign_of_current_user):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 405, 'DELETE method should not be allowed (405)'

    def test_post_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_header_and_id_of_deleted_record(self, auth_token, valid_header,
                                                            sms_campaign_of_current_user,
                                                            campaign_valid_data):
        """
        User auth token is valid. It deletes the campaign from database and then tries
        to update the record. It should get Not Found error.
        :return:
        """
        response_delete = requests.delete(
            SMS_CAMPAIGN_WITH_ID_URL % sms_campaign_of_current_user.id, headers=valid_header)
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_post = requests.post(SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
                                      headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 404, 'Record should not be found (404)'

    def test_post_with_valid_token_and_no_smartlist_associated(self, auth_token,
                                                                sms_campaign_of_current_user,
                                                                campaign_valid_data):
        """
        User auth token is valid but given sms campaign has no associated smart list with it.
        It should raise Forbidden error
        :return:
        """
        response_post = requests.post(
            SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 403, 'It should get forbidden error (403)'
