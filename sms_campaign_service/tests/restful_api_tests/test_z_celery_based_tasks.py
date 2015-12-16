"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests of tasks that run on Celery. These tests are put in
    separate file such that these tests run at the end of all tests because they needed to
    add time.sleep() due to background processing of Celery. If they run at the in the
    end. we do not need to add time.sleep()
"""

SLEEP_TIME = 15  # due to background processing of tasks (Celery)
# Standard Library
import time

# Third Party
import requests

# Application Specific
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.utils.activity_utils import CAMPAIGN_SMS_REPLY
from sms_campaign_service.tests.test_sms_receive import get_replies_count, get_reply_text
from sms_campaign_service.tests.conftest import (assert_on_blasts_sends_url_conversion_and_activity,
                                                 assert_for_activity)


class TestCeleryTasks(object):
    """
    This class contains tasks that run on celery or if  the fixture they use has some
    processing on Celery.
    """
    def test_post_with_valid_token_one_smartlist_two_candidates_with_different_phones_multiple_links_in_text(
            self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates. Body text of SMS campaign has multiple URL links
        present.
        :return:
        """
        campaign = SmsCampaign.get_by_id(str(sms_campaign_of_current_user.id))
        campaign.update(sms_body_text='Hi,all please visit http://www.abc.com or '
                                      'http://www.123.com or http://www.xyz.com')
        response_post = requests.post(
            SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 200, 'Response should be ok (200)'
        assert response_post.json()['total_sends'] == 2
        assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
        time.sleep(SLEEP_TIME)  # Need to add this processing of POST request runs on celery
        assert_on_blasts_sends_url_conversion_and_activity(sample_user.id, response_post,
                                                           str(sms_campaign_of_current_user.id))

    def test_post_with_valid_token_one_smartlist_two_candidates_with_one_phone(
            self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate have no phone number associated. So, total sends should be 1.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 200, 'Response should be ok (200)'
        assert response_post.json()['total_sends'] == 1
        assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
        assert_on_blasts_sends_url_conversion_and_activity(sample_user.id, response_post,
                                                           str(sms_campaign_of_current_user.id))

    def test_post_with_valid_token_one_smartlist_two_candidates_with_different_phones_one_link_in_text(
            self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 200, 'Response should be ok (200)'
        assert response_post.json()['total_sends'] == 2
        assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
        assert_on_blasts_sends_url_conversion_and_activity(sample_user.id,
                                                           response_post,
                                                           str(sms_campaign_of_current_user.id))

    def test_post_with_valid_token_one_smartlist_two_candidates_with_different_phones_no_link_in_text(
            self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates. Body text of SMS campaign has no URL link
        present.
        :return:
        """
        campaign = SmsCampaign.get_by_id(str(sms_campaign_of_current_user.id))
        campaign.update(sms_body_text='Hi,all')
        response_post = requests.post(
            SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS % sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert response_post.status_code == 200, 'Response should be ok (200)'
        assert response_post.json()['total_sends'] == 2
        assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
        time.sleep(SLEEP_TIME)  # Need to add this processing of POST request runs on celery
        assert_on_blasts_sends_url_conversion_and_activity(sample_user.id,
                                                           response_post,
                                                           str(sms_campaign_of_current_user.id))

    def test_post_with_valid_data_with_campaign_sent(self, user_phone_1,
                                                     sms_campaign_of_current_user,
                                                     candidate_phone_1,
                                                     process_send_sms_campaign):
        """
        - This tests the endpoint /receive

        Here we make HTTP POST  request with no data, Response should be ok as this response
        is returned to Twilio API.
        Candidate is associated with an SMS campaign. Then we assert that reply has been saved
        and replies count has been incremented by 1. Finally we assert that activity has been
        created in database table 'Activity'
        :return:
        """
        reply_text = "What's the venue?"
        reply_count_before = get_replies_count(sms_campaign_of_current_user)
        response_get = requests.post(SmsCampaignApiUrl.SMS_RECEIVE,
                                     data={'To': user_phone_1.value,
                                           'From': candidate_phone_1.value,
                                           'Body': reply_text})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        time.sleep(SLEEP_TIME) # Need to add this processing of POST request runs on celery
        campaign_reply_in_db = get_reply_text(candidate_phone_1)
        assert campaign_reply_in_db.reply_body_text == reply_text
        reply_count_after = get_replies_count(sms_campaign_of_current_user)
        assert reply_count_after == reply_count_before + 1
        assert_for_activity(user_phone_1.user_id, CAMPAIGN_SMS_REPLY, campaign_reply_in_db.id)