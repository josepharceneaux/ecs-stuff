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
                                                             sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign from database and then tries
        to update the record. It should get Not Found error.
        :return:
        """
        response_delete = requests.delete(
            SMS_CAMPAIGN_WITH_ID_URL % sms_campaign_of_current_user.id, headers=valid_header)
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_post = requests.post(
            SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 404, 'Record should not be found (404)'

    def test_post_with_valid_token_and_not_owned_campaign(self, auth_token,
                                                          sms_campaign_of_other_user):
        """
        User auth token is valid but user is not owner of given sms campaign.
        It should raise Forbidden error.
        :return:
        """
        response_post = requests.post(
            SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_other_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 403, 'It should get forbidden error (403)'
        assert 'not the owner'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_valid_token_and_no_smartlist_associated(self, auth_token,
                                                               sms_campaign_of_current_user):
        """
        User auth token is valid but given sms campaign has no associated smart list with it.
        It should raise Forbidden error
        :return:
        """
        response_post = requests.post(
            SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 500, 'It should be internal server error (500)'
        assert response_post.json()['error']['code'] == 5011
        assert 'No Smartlist'.lower() in response_post.json()['error']['message'].lower()

    # def test_post_with_valid_token_and_no_smartlist_candidate(self, auth_token,
    #                                                           sms_campaign_of_current_user,
    #                                                           sms_campaign_smartlist):
    #     """
    #     User auth token is valid, campaign has one smart list associated. But smartlist has
    #     no candidate associated with it.
    #     :return:
    #     """
    #     response_post = requests.post(
    #         SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
    #         headers=dict(Authorization='Bearer %s' % auth_token))
    #     assert response_post.status_code == 500, 'It should be internal server error (500)'
    #     assert response_post.json()['error']['code'] == 5012
    #     assert 'No Candidate'.lower() in response_post.json()['error']['message'].lower()
    #
    # def test_post_with_valid_token_one_smartlist_two_candidates_with_no_phone(
    #         self, auth_token, sms_campaign_of_current_user, sms_campaign_smartlist,
    #         sample_sms_campaign_candidates):
    #     """
    #     User auth token is valid, campaign has one smart list associated. Smartlist has two
    #     candidates. Candidates have no phone number associated. So, total sends should be 0.
    #     :return:
    #     """
    #     response_post = requests.post(
    #         SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
    #         headers=dict(Authorization='Bearer %s' % auth_token))
    #     assert response_post.status_code == 200, 'Response should be ok (200)'
    #     assert response_post.json()['total_sends'] == 0
    #     assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
    #
    # def test_post_with_valid_token_one_smartlist_two_candidates_with_one_phone(
    #         self, auth_token, sms_campaign_of_current_user, sms_campaign_smartlist,
    #         sample_sms_campaign_candidates, candidate_phone_1):
    #     """
    #     User auth token is valid, campaign has one smart list associated. Smartlist has two
    #     candidates. One candidate have no phone number associated. So, total sends should be 1.
    #     :return:
    #     """
    #     response_post = requests.post(
    #         SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
    #         headers=dict(Authorization='Bearer %s' % auth_token))
    #     assert response_post.status_code == 200, 'Response should be ok (200)'
    #     assert response_post.json()['total_sends'] == 1
    #     assert str(sms_campaign_of_current_user.id) in response_post.json()['message']

    # def test_post_with_valid_token_one_smartlist_two_candidates_with_same_phone(
    #         self, auth_token, sms_campaign_of_current_user, sms_campaign_smartlist,
    #         sample_sms_campaign_candidates, candidates_with_same_phone):
    #     """
    #     User auth token is valid, campaign has one smart list associated. Smartlist has two
    #     candidates. One candidate have no phone number associated. So, total sends should be 1.
    #     :return:
    #     """
    #     response_post = requests.post(
    #         SMS_CAMPAIGN_PROCESS_SEND_URL % sms_campaign_of_current_user.id,
    #         headers=dict(Authorization='Bearer %s' % auth_token))
    #     assert response_post.status_code == 500, 'It should be internal server error (500)'
    #     assert response_post.json()['error']['code'] == 5008
