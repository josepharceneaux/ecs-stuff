"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint

                /sms_receive

    of SMS Campaign APP.
"""

# Third Party Imports
import requests

# Application Specific
from sms_campaign_service import db
from sms_campaign_service.tests.conftest import assert_for_activity
from sms_campaign_service.common.error_handling import MethodNotAllowed
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.utils.activity_utils import CAMPAIGN_SMS_REPLY
from sms_campaign_service.common.models.sms_campaign import SmsCampaignBlast, SmsCampaignReply


class TestSmsReceive:
    """
    This class contains tests for endpoint /sms_receive.
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
        response_get = requests.post(SmsCampaignApiUrl.SMS_RECEIVE, data={'To': user_phone_1.value,
                                                                          'From': candidate_phone_1.value,
                                                                          'Body': "What's the venue?"})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        campaign_reply_in_db = _get_reply_text(candidate_phone_1)
        assert not campaign_reply_in_db

    def test_post_with_valid_data_with_campaign_sent(self, user_phone_1,
                                                     sms_campaign_of_current_user,
                                                     candidate_phone_1,
                                                     process_send_sms_campaign):
        """
        POST with no data, Response should be ok as this response is returned to Twilio API.
        Candidate is associated with an SMS campaign. Then we assert that reply has been saved
        and replies count has been incremented by 1. Finally we assert that activity has been
        created in database table 'Activity'
        :return:
        """
        reply_text = "What's the venue?"
        reply_count_before = _get_replies_count(sms_campaign_of_current_user)
        response_get = requests.post(SmsCampaignApiUrl.SMS_RECEIVE, data={'To': user_phone_1.value,
                                                                          'From': candidate_phone_1.value,
                                                                          'Body': reply_text})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        campaign_reply_in_db = _get_reply_text(candidate_phone_1)
        assert campaign_reply_in_db.reply_body_text == reply_text
        reply_count_after = _get_replies_count(sms_campaign_of_current_user)
        assert reply_count_after == reply_count_before + 1
        assert_for_activity(user_phone_1.user_id, CAMPAIGN_SMS_REPLY, campaign_reply_in_db.id)


def _get_reply_text(candidate_phone):
    """
    This asserts that exact reply of candidate has been saved in database table "sms_campaign_reply"
    :param candidate_phone:
    :return:
    """
    db.session.commit()
    campaign_reply_record = SmsCampaignReply.get_by_candidate_phone_id(candidate_phone.id)
    return campaign_reply_record


def _get_replies_count(campaign):
    """
    This returns the replies counts of SMS campaign from database table 'sms_campaign_blast'
    :param campaign: SMS campaign row
    :return:
    """
    db.session.commit()
    sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
    return sms_campaign_blasts.replies
