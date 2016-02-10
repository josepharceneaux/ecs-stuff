"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/campaigns/:id/send of SMS Campaign API.
"""
# Third Party
import requests

# Service Specific
from sms_campaign_service.modules.custom_exceptions import CandidateNotFoundInUserDomain, \
    SmsCampaignApiException
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.tests.modules.common_functions import \
    (assert_on_blasts_sends_url_conversion_and_activity, assert_api_send_response)

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

    def test_post_with_id_of_deleted_record(self, access_token_first, valid_header,
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
                                      headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response_post.status_code == ResourceNotFound.http_status_code(), \
            'Record should not be found (404)'

    def test_post_with_not_owned_campaign(self, access_token_first,
                                          sms_campaign_in_other_domain):
        """
        User auth token is valid but given SMS campaign does not belong to domain
        of logged-in user. It should get Forbidden error.
        :return:
        """
        response_post = requests.post(self.URL % sms_campaign_in_other_domain.id,
                                      headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response_post.status_code == ForbiddenError.http_status_code(), \
            'It should get forbidden error (403)'

    def test_post_with_no_smartlist_associated(self, access_token_first,
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
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response_post.status_code == InvalidUsage.http_status_code(), \
            'It should be invalid usage error(400)'
        assert response_post.json()['error']['code'] == \
               CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN
        assert 'No Smartlist'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_no_smartlist_candidate(self, access_token_first,
                                              sms_campaign_of_current_user,
                                              smartlist_for_not_scheduled_campaign):
        """
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist .
        :return:
        """
        response_post = requests.post(self.URL % sms_campaign_of_current_user.id,
                                      headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response_post.status_code == InvalidUsage.http_status_code(), \
            'It should be invalid usage error (400)'
        assert response_post.json()['error']['code'] == \
               CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST
        assert 'No Candidate'.lower() in response_post.json()['error']['message'].lower()

    def test_post_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to update a campaign which does not exists in database.
        :param access_token_first:
        :return:
        """
        CampaignsCommonTests.request_with_invalid_campaign_id(SmsCampaign,
                                                              self.METHOD,
                                                              self.URL,
                                                              access_token_first,
                                                              None)

    def test_post_with_one_smartlist_two_candidates_with_no_phone(
            self, access_token_first, user_first, sms_campaign_of_current_user,
            smartlist_for_not_scheduled_campaign,
            sample_sms_campaign_candidates):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Candidates have no phone number associated. So, total sends should be 0.
        :return:
        """
        response_post = requests.post(
            self.URL % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response_post.status_code == InvalidUsage.http_status_code()
        json_resp = response_post.json()['error']
        assert str(sms_campaign_of_current_user.id) in json_resp['message']
        assert json_resp['code'] == CampaignException.NO_VALID_CANDIDATE_FOUND

    def test_pre_process_celery_task_with_two_candidates_having_same_phone(
            self, user_first, access_token_first, smartlist_for_not_scheduled_campaign,
            sms_campaign_of_current_user, sample_sms_campaign_candidates,
            candidates_with_same_phone):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have same phone numbers. It should get an empty list which
        shows candidates associated with smartlists of campaign are not valid.
        :return:
        """
        candidate_1, candidate_2 = candidates_with_same_phone
        obj = SmsCampaignBase(user_first.id)
        obj.campaign = sms_campaign_of_current_user
        assert not obj.pre_process_celery_task([candidate_1, candidate_2])

    def test_pre_process_celery_task_with_two_candidates_having_same_phone_in_diff_domain(
            self, user_first, access_token_first, sms_campaign_of_current_user,
            smartlist_for_not_scheduled_campaign, sample_sms_campaign_candidates,
            candidates_with_same_phone_in_diff_domains):
        """
        User auth token is valid. Campaign has one smart list associated. Smartlist has two
        candidates. One candidate exists in more than one domains with same phone. It should
        not get any error.
        :return:
        """
        obj = SmsCampaignBase(user_first.id)
        obj.campaign = sms_campaign_of_current_user
        candidate_1, candidate_2 = candidates_with_same_phone_in_diff_domains
        assert len(obj.pre_process_celery_task([candidate_1, candidate_2])) == 1

    def test_pre_process_celery_task_with_valid_data(
            self, user_first, access_token_first, sms_campaign_of_current_user,
            candidate_first, candidate_second, smartlist_for_not_scheduled_campaign,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers. It should not get any error.
        :return:
        """
        obj = SmsCampaignBase(user_first.id)
        obj.campaign = sms_campaign_of_current_user
        assert len(obj.pre_process_celery_task([candidate_first, candidate_second])) == 2

    def test_does_candidate_have_unique_mobile_phone_with_two_candidates_having_same_phone(
            self, access_token_first, user_first, smartlist_for_not_scheduled_campaign,
            sample_sms_campaign_candidates, candidates_with_same_phone):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have same phone numbers. It should raise custom exception
        MultipleCandidatesFound.
        :return:
        """
        try:
            candidate_1, candidate_2 = candidates_with_same_phone
            obj = SmsCampaignBase(user_first.id)
            obj.does_candidate_have_unique_mobile_phone(candidate_1)
            assert None, 'MultipleCandidatesFound exception should be raised.'
        except MultipleCandidatesFound as error:
            assert error.error_code == CampaignException.MULTIPLE_CANDIDATES_FOUND

    def test_does_candidate_have_unique_mobile_phone_with_candidate_in_other_domain(
            self, access_token_first, user_first, smartlist_for_not_scheduled_campaign,
            sample_campaign_candidate_of_other_domain, candidate_phone_in_other_domain):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has one
        candidate but candidate belongs to some other domain.
        It should raise custom exception CandidateNotFoundInUserDomain.
        :return:
        """
        try:
            candidate_1 = candidate_phone_in_other_domain.candidate
            obj = SmsCampaignBase(user_first.id)
            obj.does_candidate_have_unique_mobile_phone(candidate_1)
            assert None, 'CandidateNotFoundInUserDomain exception should be raised.'
        except CandidateNotFoundInUserDomain as error:
            assert error.error_code == SmsCampaignApiException.NO_CANDIDATE_IN_USER_DOMAIN
