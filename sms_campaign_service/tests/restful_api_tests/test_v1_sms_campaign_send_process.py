"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/send of SMS Campaign API.
"""
# Standard Imports
import requests

# Service Specific
from sms_campaign_service.modules.custom_exceptions import SmsCampaignApiException, MultipleCandidatesFound
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.tests.modules.common_functions import \
    (assert_on_blasts_sends_url_conversion_and_activity, assert_method_not_allowed,
     assert_api_send_response)

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (UnauthorizedError, ResourceNotFound,
                                                        ForbiddenError, InternalServerError)


class TestSendSmsCampaign(object):
    """
    This class contains tests for endpoint /campaigns/:id/send
    """

    def test_for_get_request(self, auth_token, sms_campaign_of_current_user):
        """
        GET method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_method_not_allowed(response, 'GET')

    def test_for_delete_request(self, auth_token, sms_campaign_of_current_user):
        """
        DELETE method is not allowed on this endpoint, should get 405 (Method not allowed)
        :param auth_token: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.delete(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_method_not_allowed(response, 'DELETE')

    def test_post_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid, it should get Unauthorized error.
        :return:
        """
        response = requests.post(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should be unauthorized (401)'

    def test_post_with_id_of_deleted_record(self, auth_token, valid_header,
                                            sms_campaign_of_current_user):
        """
        User auth token is valid. It first deletes the campaign from database and then tries
        to update the record. It should get ResourceNotFound error.
        :return:
        """
        response_delete = requests.delete(
            SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id, headers=valid_header)
        assert response_delete.status_code == 200, 'should get ok response (200)'
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == ResourceNotFound.http_status_code(), \
            'Record should not be found (404)'

    def test_post_with_not_owned_campaign(self, auth_token,
                                          sms_campaign_of_other_user):
        """
        User auth token is valid but user is not owner of given SMS campaign.
        It should get Forbidden error.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % sms_campaign_of_other_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'
        assert 'not the owner'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_no_smartlist_associated(self, auth_token,
                                               sms_campaign_of_current_user):
        """
        User auth token is valid but given SMS campaign has no associated smartlist with it. So
        up til this point we only have created a user and SMS campaign of that user (using fixtures
        passed in as params).
        It should get internal server error. Custom error should be
        NoSmartlistAssociatedWithCampaign.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == InternalServerError.http_status_code(), \
            'It should be internal server error (500)'
        assert response_post.json()['error']['code'] == \
               SmsCampaignApiException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN
        assert 'No Smartlist'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_no_smartlist_candidate(self, auth_token,
                                              sms_campaign_of_current_user,
                                              sms_campaign_smartlist):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get internal server error.
        Custom error should be NoCandidateAssociatedWithSmartlist .
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == InternalServerError.http_status_code(), \
            'It should be internal server error (500)'
        assert response_post.json()['error']['code'] == \
               SmsCampaignApiException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST
        assert 'No Candidate'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_one_smartlist_two_candidates_with_no_phone(
            self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
            sample_sms_campaign_candidates):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Candidates have no phone number associated. So, total sends should be 0.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(sample_user.id,
                                                           0,
                                                           str(sms_campaign_of_current_user.id))

    def test_pre_process_celery_task_with_two_candidates_having_same_phone(
            self, auth_token, sms_campaign_of_current_user, sample_user, sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidates_with_same_phone,
            candidate_first, candidate_second):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have same phone numbers. It should return Internal server error.
        Error code should be 5008 (MultipleCandidatesFound)
        :return:
        """
        try:
            obj = SmsCampaignBase(sample_user.id)
            obj.pre_process_celery_task([candidate_first, candidate_second])
        except MultipleCandidatesFound as error:
            assert error.error_code == SmsCampaignApiException.MULTIPLE_CANDIDATES_FOUND
