"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/receive of SMS Campaign APP.
"""
# Third Party Imports
import requests

# Common Utils
from sms_campaign_service.common.models.misc import Activity
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import InvalidUsage
from sms_campaign_service.common.campaign_services.custom_errors import (CampaignException,
                                                                         MultipleCandidatesFound)
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

# Service Specific
from sms_campaign_service.tests.conftest import fake
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.modules.custom_exceptions import (SmsCampaignApiException,
                                                            MultipleUsersFound,
                                                            CandidateNotFoundInUserDomain,
                                                            NoUserFoundForPhoneNumber,
                                                            NoSMSCampaignSentToCandidate)
from sms_campaign_service.tests.modules.common_functions import (get_reply_text,
                                                                 assert_for_activity)


class TestSmsReceive(object):
    """
    This class contains tests for endpoint /v1/receive (and all the code being used by
    this endpoint).
    """

    def test_post_with_no_data(self):
        """
        POST with no data, Response should be OK as this response is returned to Twilio API
        """
        response_get = requests.post(SmsCampaignApiUrl.RECEIVE)
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()

    def test_post_with_valid_data_no_campaign_sent(self, user_phone_1, candidate_phone_2):
        """
        POST with valid data but no campaign is sent to candidate,
        This is the case when a saved candidate sends an SMS to some recruiter's (user's)
        number and no campaign was sent to this candidate.
        Response should be OK as this response is returned to Twilio API
        """
        response_get = requests.post(SmsCampaignApiUrl.RECEIVE,
                                     data={'To': user_phone_1.value,
                                           'From': candidate_phone_2.value,
                                           'Body': "What's the venue?"})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        campaign_reply_in_db = get_reply_text(candidate_phone_2)
        assert not campaign_reply_in_db

    def test_process_candidate_reply_with_no_data(self):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is empty dict, so, it should get Internal server Error. Error code should be
        MISSING_REQUIRED_FIELD.
        """
        try:
            SmsCampaignBase.process_candidate_reply(dict())
        except InvalidUsage as error:
            assert error.status_code == CampaignException.MISSING_REQUIRED_FIELD
            assert 'From' in error.message
            assert 'To' in error.message
            assert 'Body' in error.message

    def test_process_candidate_reply_with_no_campaign_sent(self,
                                                           user_phone_1,
                                                           candidate_phone_2):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but no campaign is sent to candidate. So, it should get
        NoSMSCampaignSentToCandidate Error.
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     'From': candidate_phone_2.value,
                                                     'Body': "What's the venue?"})
        except NoSMSCampaignSentToCandidate as error:
            assert error.error_code == SmsCampaignApiException.NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE
            assert str(candidate_phone_2.candidate_id) in error.message

    def test_process_candidate_reply_with_unknown_candidate_phone(self, user_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but candidate phone is not saved in database.
        This is the case when candidate does not exist in getTalent database.
        It should get CandidateNotFoundInUserDomain custom exception.
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     # unknown candidate phone
                                                     'From': fake.phone_number(),
                                                     'Body': "What's the venue?"})
        except CandidateNotFoundInUserDomain as error:
            assert error.error_code == SmsCampaignApiException.NO_CANDIDATE_IN_USER_DOMAIN

    def test_process_candidate_reply_with_candidate_of_other_domain(
            self, user_phone_1, candidate_phone_in_other_domain):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but candidate phone belongs to other domain.
        This is the case when candidate does not exist in getTalent database.
        It should get NO_CANDIDATE_IN_USER_DOMAIN custom error.
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     'From': candidate_phone_in_other_domain.value,
                                                     'Body': "What's the venue?"})
        except CandidateNotFoundInUserDomain as error:
            assert error.error_code == SmsCampaignApiException.NO_CANDIDATE_IN_USER_DOMAIN

    def test_process_candidate_reply_with_multiple_candidates_having_same_phone(
            self, user_phone_1, candidates_with_same_phone):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but phone number of candidate is associated with multiple
        candidates. It should get MULTIPLE_CANDIDATES_FOUND custom exception.
        """
        try:
            SmsCampaignBase.process_candidate_reply(
                {'To': user_phone_1.value,
                 'From': candidates_with_same_phone[0].phones[0].value,
                 'Body': "What's the venue?"})
        except MultipleCandidatesFound as error:
            assert error.error_code == CampaignException.MULTIPLE_CANDIDATES_FOUND

    def test_process_candidate_reply_with_multiple_users_having_same_phone(self,
                                                                           users_with_same_phone,
                                                                           candidate_phone_2):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but user phone is associated with multiple users. It should get
        MultipleUsersFound custom exception.
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': users_with_same_phone[0].value,
                                                     'From': candidate_phone_2.value,
                                                     'Body': "What's the venue?"})
        except MultipleUsersFound as error:
            assert error.error_code == SmsCampaignApiException.MULTIPLE_USERS_FOUND

    def test_process_candidate_reply_with_no_user_associated_with_phone(self, candidate_phone_2):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but user phone is associated with no users. It should get
        NO_USER_FOR_PHONE_NUMBER custom exception.
        """
        try:
            SmsCampaignBase.process_candidate_reply(
                {'To': fake.phone_number(),  # Unknown user phone
                 'From': candidate_phone_2.value,
                 'Body': "What's the venue?"})
        except NoUserFoundForPhoneNumber as error:
            assert error.error_code == SmsCampaignApiException.NO_USER_FOR_PHONE_NUMBER

    def test_sms_receive_with_valid_data_and_one_campaign_sent(
            self, user_phone_1, sent_campaign, access_token_first, candidate_and_phone_1):
        """
        - This tests the endpoint /v1/receive

        Here we make HTTP POST  request with no data, Response should be OK as this response
        is returned to Twilio API.
        Candidate is associated with an SMS campaign. Then we assert that reply has been saved
        and replies count has been incremented by 1. Finally we assert that activity has been
        created in database table 'Activity'.
        """
        _assert_valid_response(sent_campaign, user_phone_1, candidate_and_phone_1[1], access_token_first)

    def test_sms_receive_with_candidate_having_same_phone_in_diff_domains(
            self, user_phone_1, candidates_with_same_phone_in_diff_domains,
            sent_campaign, access_token_first, candidate_and_phone_1):
        """
        - This tests the endpoint /v1/receive

        Data passed is valid and candidate belongs to more than one domains.
        It should not get any error.
        """

        _assert_valid_response(sent_campaign, user_phone_1, candidate_and_phone_1[1], access_token_first)


def get_replies_count(campaign, access_token):
    """
    This returns the replies counts of SMS campaign from database table 'sms_campaign_blast'
    :param campaign: SMS campaign obj
    :param access_token: Access token of user
    """
    sms_campaign_blasts = CampaignsTestsHelpers.get_blasts_with_polling(campaign,
                                                                        access_token,
                                                                        blasts_url=SmsCampaignApiUrl.BLASTS % campaign['id'])
    return sms_campaign_blasts[0]['replies']


def _assert_valid_response(campaign_obj, user_phone, candidate_phone, access_token):
    """
    Here is the functionality to test valid response on given campaign
    """
    reply_text = "What's the venue?"
    reply_count_before = get_replies_count(campaign_obj, access_token)
    response_get = requests.post(SmsCampaignApiUrl.RECEIVE,
                                 data={'To': user_phone.value,
                                       'From': candidate_phone['value'],
                                       'Body': reply_text})
    assert response_get.status_code == 200, 'Response should be ok'
    assert 'xml' in str(response_get.text).strip()
    campaign_reply_in_db = get_reply_text(candidate_phone)
    assert len(campaign_reply_in_db) == 1
    assert campaign_reply_in_db[0].body_text == reply_text
    reply_count_after = get_replies_count(campaign_obj, access_token)
    assert reply_count_after == reply_count_before + 1
    assert_for_activity(user_phone.user_id, Activity.MessageIds.CAMPAIGN_SMS_REPLY,
                        campaign_reply_in_db[0].id)
