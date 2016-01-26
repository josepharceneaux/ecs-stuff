"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/send of SMS Campaign API.
"""
# Third Party
import requests

# Service Specific
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.tests.modules.common_functions import \
    (assert_on_blasts_sends_url_conversion_and_activity, assert_method_not_allowed,
     assert_api_send_response)

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.error_handling import (UnauthorizedError, ResourceNotFound,
                                                        ForbiddenError, InvalidUsage)
from sms_campaign_service.common.campaign_services.common_tests import CampaignsCommonTests
from sms_campaign_service.common.campaign_services.custom_errors import (CampaignException,
                                                                         MultipleCandidatesFound)


class TestSendSmsCampaign(object):
    """
    This class contains tests for endpoint /campaigns/:id/send
    """
    URL = SmsCampaignApiUrl.SEND
    METHOD = 'post'

    def test_post_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid, it should get Unauthorized error.
        :return:
        """
        response = requests.post(self.URL % sms_campaign_of_current_user.id,
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
        response_post = requests.post(self.URL % sms_campaign_of_current_user.id,
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
        response_post = requests.post(self.URL % sms_campaign_of_other_user.id,
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
        It should get Invalid usage error. Custom error should be
        NoSmartlistAssociatedWithCampaign.
        :return:
        """
        response_post = requests.post(
            self.URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == InvalidUsage.http_status_code(), \
            'It should be invalid usage error(400)'
        assert response_post.json()['error']['code'] == \
               CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN
        assert 'No Smartlist'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_no_smartlist_candidate(self, auth_token,
                                              sms_campaign_of_current_user,
                                              smartlist_for_not_scheduled_campaign):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist .
        :return:
        """
        response_post = requests.post(self.URL % sms_campaign_of_current_user.id,
                                      headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == InvalidUsage.http_status_code(), \
            'It should be invalid usage error (400)'
        assert response_post.json()['error']['code'] == \
               CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST
        assert 'No Candidate'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_invalid_campaign_id(self, auth_token):
        """
        This is a test to update a campaign which does not exists in database.
        :param auth_token:
        :return:
        """
        CampaignsCommonTests.request_with_invalid_campaign_id(SmsCampaign,
                                                              self.METHOD,
                                                              self.URL,
                                                              auth_token,
                                                              None)

    def test_post_with_one_smartlist_two_candidates_with_no_phone(
            self, auth_token, sample_user, sms_campaign_of_current_user,
            smartlist_for_not_scheduled_campaign,
            sample_sms_campaign_candidates):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Candidates have no phone number associated. So, total sends should be 0.
        :return:
        """
        response_post = requests.post(
            self.URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 0, sms_campaign_of_current_user)

    def test_pre_process_celery_task_with_two_candidates_having_same_phone(
            self, auth_token, sample_user, smartlist_for_not_scheduled_campaign,
            sample_sms_campaign_candidates, candidates_with_same_phone, candidate_first,
            candidate_second):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have same phone numbers. It should raise custom exception
        MultipleCandidatesFound.
        :return:
        """
        try:
            obj = SmsCampaignBase(sample_user.id)
            obj.pre_process_celery_task([candidate_first, candidate_second])
            assert None, 'MultipleCandidatesFound exception should be raised.'
        except MultipleCandidatesFound as error:
            assert error.error_code == CampaignException.MULTIPLE_CANDIDATES_FOUND

    def test_pre_process_celery_task_with_valid_data(
            self, sample_user, auth_token, sms_campaign_of_current_user,
            candidate_first, candidate_second, smartlist_for_not_scheduled_campaign,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers. It should not get any error.
        :return:
        """
        obj = SmsCampaignBase(sample_user.id)
        obj.campaign = sms_campaign_of_current_user
        assert obj.pre_process_celery_task([candidate_first, candidate_second])


def test_for_get_request(auth_token, sms_campaign_of_current_user):
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


def test_for_delete_request(auth_token, sms_campaign_of_current_user):
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
