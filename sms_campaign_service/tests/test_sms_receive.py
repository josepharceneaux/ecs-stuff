"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint

                /v1/receive

    of SMS Campaign APP.
"""
# Third Party Imports
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl

# Service Specific
from sms_campaign_service.tests.conftest import fake
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.tests.modules.common_functions import (get_reply_text,
                                                                 assert_method_not_allowed)


class TestSmsReceive(object):
    """
    This class contains tests for endpoint /v1/receive (and all the code being used by
    this endpoint).
    """

    def test_for_get(self):
        """
        GET method should not be allowed at this endpoint.
        :return:
        """
        response = requests.get(SmsCampaignApiUrl.RECEIVE)
        assert_method_not_allowed(response, 'GET')

    def test_for_delete(self):
        """
        DELETE method should not be allowed at this endpoint.
        :return:
        """
        response = requests.delete(SmsCampaignApiUrl.RECEIVE)
        assert_method_not_allowed(response, 'DELETE')

    def test_post_with_no_data(self):
        """
        POST with no data, Response should be OK as this response is returned to Twilio API
        :return:
        """
        response_get = requests.post(SmsCampaignApiUrl.RECEIVE)
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()

    def test_post_with_valid_data_no_campaign_sent(self, user_phone_1,
                                                   candidate_phone_1
                                                   ):
        """
        POST with valid data but no campaign is sent to candidate,
        This is the case when a saved candidates sends an SMS to some recruiter's (user's)
        number and no campaign was sent to this candidate.
        Response should be OK as this response is returned to Twilio API
        :return:
        """
        response_get = requests.post(SmsCampaignApiUrl.RECEIVE,
                                     data={'To': user_phone_1.value,
                                           'From': candidate_phone_1.value,
                                           'Body': "What's the venue?"})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        campaign_reply_in_db = get_reply_text(candidate_phone_1)
        assert not campaign_reply_in_db

    def test_process_candidate_reply_with_no_data(self):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is empty dict, so, it should get MissingRequiredField Error.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply(dict())
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.MISSING_REQUIRED_FIELD
            assert 'From' in error.message
            assert 'To' in error.message
            assert 'Body' in error.message

    def test_process_candidate_reply_with_no_campaign_sent(self,
                                                           user_phone_1,
                                                           candidate_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but no campaign is sent to candidate. So, it should get
        NoSMSCampaignSentToCandidate Error.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     'From': candidate_phone_1.value,
                                                     'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.NO_SMS_CAMPAIGN_SENT_TO_CANDIDATE
            assert str(candidate_phone_1.candidate_id) in error.message

    def test_process_candidate_reply_with_no_candidate_phone_saved(self,
                                                                   user_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but candidate phone is not saved in database.
        This is the case when candidate does not exist in getTalent database.
        It should get NoCandidateForPhoneNumber custom exception.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     # unknown candidate phone
                                                     'From': fake.phone_number(),
                                                     'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.NO_CANDIDATE_FOR_PHONE_NUMBER

    def test_process_candidate_reply_with_multiple_candidates_having_same_phone(self,
                                                                                user_phone_1,
                                                                                candidates_with_same_phone):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but phone number of candidate is associated with multiple
        candidates. It should get MULTIPLE_CANDIDATES_FOUND custom exception.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     'From': candidates_with_same_phone[0].value,
                                                     'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.MULTIPLE_CANDIDATES_FOUND

    def test_process_candidate_reply_with_multiple_users_having_same_phone(self,
                                                                           users_with_same_phone,
                                                                           candidate_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but user phone is associated with multiple users. It should get
        MultipleUsersFound custom exception.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': users_with_same_phone[0].value,
                                                     'From': candidate_phone_1.value,
                                                     'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.MULTIPLE_USERS_FOUND

    def test_process_candidate_reply_with_no_user_associated_with_phone(self,
                                                                        candidate_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but user phone is associated with no users. It should get
        NO_USER_FOR_PHONE_NUMBER custom exception.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply(
                {'To': fake.phone_number(),  # Unknown user phone
                 'From': candidate_phone_1.value,
                 'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.NO_USER_FOR_PHONE_NUMBER
