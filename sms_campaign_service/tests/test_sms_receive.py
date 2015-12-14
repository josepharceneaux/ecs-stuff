"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint

                /receive

    of SMS Campaign APP.
"""

# Third Party Imports
import requests

# Application Specific
from sms_campaign_service import db
from sms_campaign_service.common.error_handling import MethodNotAllowed
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaignBlast, SmsCampaignReply


class TestSmsReceive:
    """
    This class contains tests for endpoint /receive.
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


def get_reply_text(candidate_phone):
    """
    This asserts that exact reply of candidate has been saved in database table "sms_campaign_reply"
    :param candidate_phone:
    :return:
    """
    db.session.commit()
    campaign_reply_record = SmsCampaignReply.get_by_candidate_phone_id(candidate_phone.id)
    return campaign_reply_record


def get_replies_count(campaign):
    """
    This returns the replies counts of SMS campaign from database table 'sms_campaign_blast'
    :param campaign: SMS campaign row
    :return:
    """
    db.session.commit()
    sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
    return sms_campaign_blasts.replies
