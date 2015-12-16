"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint

                /v1/receive

    of SMS Campaign APP.
"""
# Third Party Imports
import requests

# Standard Imports
from werkzeug.security import gen_salt

# Common Utils
from sms_campaign_service.common.error_handling import MethodNotAllowed
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl

# Service Specific
from sms_campaign_service.tests.conftest import get_reply_text
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.custom_exceptions import SmsCampaignApiException


class TestSmsReceive(object):
    """
    This class contains tests for endpoint /v1/receive.
    """

    def test_for_get(self):
        """
        GET method should not be allowed at this endpoint.
        :return:
        """
        response_post = requests.get(SmsCampaignApiUrl.SMS_RECEIVE)
        assert response_post.status_code == MethodNotAllowed.http_status_code(), \
            'GET Method should not be allowed'

    def test_for_delete(self):
        """
        DELETE method should not be allowed at this endpoint.
        :return:
        """
        response_post = requests.delete(SmsCampaignApiUrl.SMS_RECEIVE)
        assert response_post.status_code == MethodNotAllowed.http_status_code(), \
            'DELETE Method should not be allowed'

    def test_post_with_no_data(self):
        """
        POST with no data, Response should be ok as this response is returned to Twilio API
        :return:
        """
        response_get = requests.post(SmsCampaignApiUrl.SMS_RECEIVE)
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()

    def test_post_with_valid_data_no_campaign_sent(self, user_phone_1,
                                                   candidate_phone_1
                                                   ):
        """
        POST with no data, Response should be ok as this response is returned to Twilio API
        :return:
        """
        response_get = requests.post(SmsCampaignApiUrl.SMS_RECEIVE,
                                     data={'To': user_phone_1.value,
                                           'From': candidate_phone_1.value,
                                           'Body': "What's the venue?"})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        campaign_reply_in_db = get_reply_text(candidate_phone_1)
        assert not campaign_reply_in_db

    def test_method_process_candidate_reply_with_No_data(self):
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

    def test_method_process_candidate_reply_with_no_campaign_sent(self,
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

    def test_method_process_candidate_reply_with_no_candidate_phone_saved(self,
                                                                          user_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but candidate phone is not saved in database. It should get
        NO_CANDIDATE_FOR_PHONE_NUMBER custom exception.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': user_phone_1.value,
                                                     # unknown candidate phone
                                                     'From': gen_salt(15),
                                                     'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.NO_CANDIDATE_FOR_PHONE_NUMBER

    def test_method_process_candidate_reply_with_multiple_candidates_having_same_phone(self,
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

    def test_method_process_candidate_reply_with_multiple_users_having_same_phone(self,
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

    def test_method_process_candidate_reply_with_no_user_associated_with_phone(self,
                                                                               candidate_phone_1):
        """
        This tests the functionality of process_candidate_reply() class method of SmsCampaignBase.
        Data passed is valid, but user phone is associated with no users. It should get
        NO_USER_FOR_PHONE_NUMBER custom exception.
        :return:
        """
        try:
            SmsCampaignBase.process_candidate_reply({'To': gen_salt(15),  # Unknown user phone
                                                     'From': candidate_phone_1.value,
                                                     'Body': "What's the venue?"})
        except Exception as error:
            assert error.error_code == SmsCampaignApiException.NO_USER_FOR_PHONE_NUMBER


