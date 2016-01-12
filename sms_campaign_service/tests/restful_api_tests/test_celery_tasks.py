"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests of tasks that run on Celery. These tests are put in
    separate file such that these tests run at the end of all tests because they needed to
    add time.sleep() due to background processing of Celery.

    This module also contains pyTests for endpoint
                /v1/redirect/:id
    of SMS Campaign API.
"""

# Standard Library
import json
import time
import urllib
from datetime import datetime, timedelta

# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.utils.handy_functions import to_utc_str
from sms_campaign_service.common.utils.activity_utils import ActivityMessageIds
from sms_campaign_service.common.error_handling import (ResourceNotFound,
                                                        InternalServerError,
                                                        MethodNotAllowed, InvalidUsage)
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.campaign_services.campaign_utils import (FrequencyIds,
                                                                          delete_scheduled_task)
from sms_campaign_service.common.campaign_services.validators import \
    validate_blast_candidate_url_conversion_in_db

# Database Models
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.models.candidate import Candidate
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)

# Service Specific
from sms_campaign_service.common.models.db import db
from sms_campaign_service.tests.conftest import app
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.modules.handy_functions import replace_ngrok_link_with_localhost
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.tests.modules.common_functions import \
    (assert_on_blasts_sends_url_conversion_and_activity, assert_for_activity, get_reply_text,
     assert_api_send_response, assert_campaign_schedule, SLEEP_TIME)


class TestCeleryTasks(object):
    """
    This class contains tasks that run on celery or if  the fixture they use has some
    processing on Celery.
    """

    def test_campaign_send_with_two_candidates_with_different_phones_multiple_links_in_text(
            self, auth_token, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates. Body text of SMS campaign has multiple URLs
        present.
        :return:
        """
        campaign = SmsCampaign.get_by_id(str(scheduled_sms_campaign_of_current_user.id))
        campaign.update(body_text='Hi,all please visit http://www.abc.com or '
                                  'http://www.123.com or http://www.xyz.com')
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 2, str(scheduled_sms_campaign_of_current_user.id))

    def test_campaign_send_with_two_candidates_with_valid_and_invalid_phones(
            self, auth_token, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sample_sms_campaign_candidates, candidate_phone_1,
            candidate_invalid_phone):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate has invalid phone number associated, other has valid phone number
        associated. So, total sends should be 1.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        # as one phone number is invalid, so only one record should be enter in sms_campaign_send
        # and sms_campaign_blast.sends should be equal to 1.
        # Expected send is 1.
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 1, str(scheduled_sms_campaign_of_current_user.id))

    def test_campaign_send_with_two_candidates_with_one_phone(
            self, auth_token, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sample_sms_campaign_candidates, candidate_phone_1):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate have no phone number associated. So, total sends should be 1.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 1, str(scheduled_sms_campaign_of_current_user.id))

    def test_campaign_send_with_two_candidates_having_different_phones_one_link_in_text(
            self, auth_token, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smartlist associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 2, str(scheduled_sms_campaign_of_current_user.id))

    def test_campaign_send_with_two_candidates_with_different_phones_no_link_in_text(
            self, auth_token, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist,
            sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates. Body text of SMS campaign has no URL link
        present.
        :return:
        """
        campaign = SmsCampaign.get_by_id(str(scheduled_sms_campaign_of_current_user.id))
        campaign.update(body_text='Hi,all')
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 2, str(scheduled_sms_campaign_of_current_user.id))

    def test_campaign_send_with_multiple_smartlists(
            self, auth_token, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sms_campaign_smartlist_2, sample_sms_campaign_candidates,
            candidate_phone_1):
        """
        - This tests the endpoint /v1/campaigns/:id/send

        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate have no phone number associated. So, total sends should be 1.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % auth_token))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 1, str(scheduled_sms_campaign_of_current_user.id))

    def test_schedule_periodic_campaign_with_past_end_date(
            self, valid_header, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sample_sms_campaign_candidates, candidate_phone_1):
        """
        This is test to schedule SMS campaign with all valid parameters. This should get OK
         response
        """
        data = generate_campaign_schedule_data()
        data['frequency_id'] = FrequencyIds.DAILY  # for Periodic job
        data['end_datetime'] = to_utc_str(datetime.utcnow() - timedelta(hours=SLEEP_TIME))
        response = requests.post(
            SmsCampaignApiUrl.SCHEDULE % scheduled_sms_campaign_of_current_user.id,
            headers=valid_header, data=json.dumps(data))
        assert response.status_code == InvalidUsage.http_status_code()

    def test_sms_receive_with_valid_data_and_one_campaign_sent(
            self, user_phone_1, scheduled_sms_campaign_of_current_user,
            candidate_phone_1, process_send_sms_campaign):
        """
        - This tests the endpoint /v1/receive

        Here we make HTTP POST  request with no data, Response should be OK as this response
        is returned to Twilio API.
        Candidate is associated with an SMS campaign. Then we assert that reply has been saved
        and replies count has been incremented by 1. Finally we assert that activity has been
        created in database table 'Activity'
        :return:
        """
        reply_text = "What's the venue?"
        reply_count_before = get_replies_count(scheduled_sms_campaign_of_current_user)
        response_get = requests.post(SmsCampaignApiUrl.RECEIVE,
                                     data={'To': user_phone_1.value,
                                           'From': candidate_phone_1.value,
                                           'Body': reply_text})
        assert response_get.status_code == 200, 'Response should be ok'
        assert 'xml' in str(response_get.text).strip()
        campaign_reply_in_db = get_reply_text(candidate_phone_1)
        assert campaign_reply_in_db.body_text == reply_text
        reply_count_after = get_replies_count(scheduled_sms_campaign_of_current_user)
        assert reply_count_after == reply_count_before + 1
        assert_for_activity(user_phone_1.user_id, ActivityMessageIds.CAMPAIGN_SMS_REPLY,
                            campaign_reply_in_db.id)


def get_replies_count(campaign):
    """
    This returns the replies counts of SMS campaign from database table 'sms_campaign_blast'
    :param campaign: SMS campaign obj
    :return:
    """
    db.session.commit()
    sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
    return sms_campaign_blasts.replies


class TestCampaignSchedule(object):
    """
    This is the test for scheduling a campaign ans verify it is sent to candidate as
    per send time.
    """

    def test_campaign_schedule_and_validate_one_time_task_run(
            self, valid_header, sample_user, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sample_sms_campaign_candidates, candidate_phone_1):
        """
        This is test to schedule SMS campaign with all valid parameters. This should get OK
         response
        """
        response = requests.post(
            SmsCampaignApiUrl.SCHEDULE % scheduled_sms_campaign_of_current_user.id,
            headers=valid_header, data=json.dumps(generate_campaign_schedule_data()))
        task_id = assert_campaign_schedule(response)
        time.sleep(SLEEP_TIME)
        assert_on_blasts_sends_url_conversion_and_activity(
            sample_user.id, 1, str(scheduled_sms_campaign_of_current_user.id))
        _delete_scheduled_task(task_id, valid_header)

# TODO: add test for periodic job as well when we have configurable frequency in scheduler_service


def _delete_scheduled_task(task_id, headers):
    """
    This deletes the scheduled task from scheduler_service
    :param task_id:
    :param headers:
    :return:
    """
    with app.app_context():
        delete_scheduled_task(task_id, headers)


# class TestSmsCampaignURLRedirection(object):
#     """
#     This class contains tests for endpoint /v1/redirect/:id
#     """
#
#     def test_for_post(self, url_conversion_by_send_test_sms_campaign):
#         """
#         POST method should not be allowed at this endpoint.
#         :return:
#         """
#         response_post = requests.post(url_conversion_by_send_test_sms_campaign.source_url)
#         # TODO: remove this when app is up
#         if response_post.status_code == ResourceNotFound.http_status_code():
#             localhost_url = replace_ngrok_link_with_localhost(
#                 url_conversion_by_send_test_sms_campaign.source_url)
#             response_post = requests.post(localhost_url)
#         assert response_post.status_code == MethodNotAllowed.http_status_code(), \
#             'POST Method should not be allowed'
#
#     def test_for_delete(self, url_conversion_by_send_test_sms_campaign):
#         """
#         DELETE method should not be allowed at this endpoint.
#         :return:
#         """
#         response_post = requests.delete(url_conversion_by_send_test_sms_campaign.source_url)
#         # TODO: remove this when app is up
#         if response_post.status_code == ResourceNotFound.http_status_code():
#             localhost_url = replace_ngrok_link_with_localhost(
#                 url_conversion_by_send_test_sms_campaign.source_url)
#             response_post = requests.delete(localhost_url)
#
#         assert response_post.status_code == MethodNotAllowed.http_status_code(), \
#             'DELETE Method should not be allowed'
#
#     def test_for_get(self, sample_user,
#                      url_conversion_by_send_test_sms_campaign,
#                      scheduled_sms_campaign_of_current_user):
#         """
#         GET method should give OK response. We check the "hit_count" and "clicks" before
#         hitting the endpoint and after hitting the endpoint. Then we assert that both
#         "hit_count" and "clicks" have been successfully updated by '1' in database.
#         :return:
#         """
#         # stats before making HTTP GET request to source URL
#         hit_count, clicks = _get_hit_count_and_clicks(url_conversion_by_send_test_sms_campaign,
#                                                       scheduled_sms_campaign_of_current_user)
#         response_get = _use_ngrok_or_local_address(
#             url_conversion_by_send_test_sms_campaign.source_url)
#         assert response_get.status_code == 200, 'Response should be ok'
#         # stats after making HTTP GET request to source URL
#         hit_count_after, clicks_after = _get_hit_count_and_clicks(
#             url_conversion_by_send_test_sms_campaign,
#             scheduled_sms_campaign_of_current_user)
#         assert hit_count_after == hit_count + 1
#         assert clicks_after == clicks + 1
#         assert_for_activity(sample_user.id, ActivityMessageIds.CAMPAIGN_SMS_CLICK,
#                             scheduled_sms_campaign_of_current_user.id)
#
#     def test_get_with_no_sigature(self, url_conversion_by_send_test_sms_campaign):
#         """
#         Removing signature of signed redirect URL. It should get internal server error.
#         :return:
#         """
#         url_excluding_signature = \
#             url_conversion_by_send_test_sms_campaign.source_url.split('?')[0]
#         response_get = _use_ngrok_or_local_address(url_excluding_signature)
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get internal server error'
#
#     def test_get_with_empty_destination_url(self, url_conversion_by_send_test_sms_campaign):
#         """
#         Making destination URL an empty string here, it should get internal server error.
#         :return:
#         """
#         # forcing destination URL to be empty
#         url_conversion_by_send_test_sms_campaign.update(destination_url='')
#         response_get = _use_ngrok_or_local_address(
#             url_conversion_by_send_test_sms_campaign.source_url)
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get internal server error'
#
#     def test_get_with_deleted_campaign(
#             self, valid_header, scheduled_sms_campaign_of_current_user,
#             url_conversion_by_send_test_sms_campaign):
#         """
#         Here we first delete the campaign, and then test functionality of process_url_redirect
#         by making HTTP GET call to endpoint /v1/redirect. It should give ResourceNotFound Error.
#         But candidate should get Internal server error. Hence this test should get internal server
#         error.
#         """
#         _delete_sms_campaign(scheduled_sms_campaign_of_current_user, valid_header)
#         response_get = _use_ngrok_or_local_address(
#             url_conversion_by_send_test_sms_campaign.source_url)
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get Internal server error'
#
#     def test_get_with_deleted_candidate(self, url_conversion_by_send_test_sms_campaign,
#                                         candidate_first):
#         """
#         Here we first delete the candidate, which internally deletes the sms_campaign_send record
#         as it uses candidate as primary key. We then test functionality of process_url_redirect
#         by making HTTP GET call to endpoint /v1/redirect. It should get ResourceNotFound Error.
#         But candidate should only get internal server error. So this test asserts we get internal
#         server error.
#         """
#         _delete_candidate(candidate_first)
#         response_get = _use_ngrok_or_local_address(
#             url_conversion_by_send_test_sms_campaign.source_url)
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get Internal server error'
#
#     def test_get_with_deleted_url_conversion(self, url_conversion_by_send_test_sms_campaign):
#         """
#         Here we first delete the url_conversion object. which internally deletes the
#         sms_campaign_send record as it uses url_conversion as primary key. We then test
#         functionality of process_url_redirect by making HTTP GET call to endpoint /v1/redirect.
#         It should get ResourceNotFound Error. But candidate should only get internal server error.
#         So this test asserts we get internal server error.
#         """
#         source_url = url_conversion_by_send_test_sms_campaign.source_url
#         _delete_url_conversion(url_conversion_by_send_test_sms_campaign)
#         response_get = _use_ngrok_or_local_address(source_url)
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get Internal server error'
#
#     def test_validate_blast_candidate_url_conversion_in_db_with_no_candidate(
#             self, scheduled_sms_campaign_of_current_user,
#             url_conversion_by_send_test_sms_campaign):
#         """
#         Here we first delete the candidate, and then test functionality of
#         validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
#         It should give ResourceNotFound Error.
#         """
#         blast_obj = SmsCampaignBlast.get_by_campaign_id(scheduled_sms_campaign_of_current_user.id)
#         _test_validate_blast_candidate_url_conversion_in_db(
#             blast_obj, None, url_conversion_by_send_test_sms_campaign)
#
#     def test_validate_blast_candidate_url_conversion_in_db_with_no_blast(
#             self, candidate_first, url_conversion_by_send_test_sms_campaign):
#         """
#         Here we pass blast as None, and then test functionality of
#         validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
#         It should give ResourceNotFound Error.
#         """
#         _test_validate_blast_candidate_url_conversion_in_db(
#             None, candidate_first, url_conversion_by_send_test_sms_campaign)
#
#     def test_validate_blast_candidate_url_conversion_in_db_with_no_url_conversion(
#             self, candidate_first, scheduled_sms_campaign_of_current_user):
#         """
#         Here we pass url_conversion obj  as None, and then test functionality of
#         validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
#         It should give ResourceNotFound Error.
#         """
#         blast_obj = SmsCampaignBlast.get_by_campaign_id(scheduled_sms_campaign_of_current_user.id)
#         _test_validate_blast_candidate_url_conversion_in_db(
#             blast_obj, candidate_first, None)
#
#     def test_pre_process_url_redirect_with_empty_data(self):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
#         All parameters passed are None, So, it should raise Invalid Usage Error.
#         :return:
#         """
#         try:
#             CampaignBase.pre_process_url_redirect({}, None)
#         except InvalidUsage as error:
#             assert error.status_code == InvalidUsage.http_status_code()
#
#     def test_pre_process_url_redirect_with_valid_data(self,
#                                                       url_conversion_by_send_test_sms_campaign):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
#         All parameters passed are valid, So, it should get OK response.
#         :param url_conversion_by_send_test_sms_campaign:
#         :return:
#         """
#         try:
#             request_args = _get_args_from_url(url_conversion_by_send_test_sms_campaign.source_url)
#             with app.app_context():
#                 SmsCampaignBase.pre_process_url_redirect(
#                     request_args, url_conversion_by_send_test_sms_campaign.source_url)
#         except Exception as error:
#             assert not error.message, 'Pre Processing should not raise any error'
#
#     def test_pre_process_url_redirect_with_missing_key_signature(
#             self, url_conversion_by_send_test_sms_campaign, candidate_first):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
#         signature is missing from request_arg.So, it should get Invalid Usage Error.
#         :param url_conversion_by_send_test_sms_campaign:
#         :param candidate_first:
#         :return:
#         """
#         try:
#             request_args = _get_args_from_url(url_conversion_by_send_test_sms_campaign.source_url)
#             del request_args['signature']
#             with app.app_context():
#                 SmsCampaignBase.pre_process_url_redirect(
#                     request_args, url_conversion_by_send_test_sms_campaign.source_url)
#         except InvalidUsage as error:
#             assert error.status_code == InvalidUsage.http_status_code()
#
#
# def _delete_sms_campaign(campaign, header):
#     """
#     This calls the API /campaigns/:id to delete the given campaign
#     :param campaign:
#     :param header:
#     :return:
#     """
#     response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % campaign.id,
#                                headers=header)
#     db.session.commit()
#     assert response.status_code == 200, 'should get ok response (200)'
#
#
# def _delete_candidate(candidate_first):
#     """
#     This deletes the candidate of given id
#     :param candidate_first:
#     :return:
#     """
#     Candidate.delete(candidate_first)
#
#
# def _delete_url_conversion(url_conversion_obj):
#     """
#     This deletes the candidate of given id
#     :param url_conversion_obj:
#     :return:
#     """
#     UrlConversion.delete(url_conversion_obj)
#
#
# def _test_validate_blast_candidate_url_conversion_in_db(blast, candidate, url_conversion_obj):
#     """
#     This tests the functionality of validate_blast_candidate_url_conversion_in_db() method in
#         campaign_utils.py.
#     :param blast:
#     :param candidate:
#     :param url_conversion_obj:
#     :return:
#     """
#     try:
#         validate_blast_candidate_url_conversion_in_db(blast, candidate, url_conversion_obj)
#         assert None, 'It should get resource not found error'
#     except ResourceNotFound as error:
#         assert error.status_code == ResourceNotFound.http_status_code(), \
#             'It should get Resource not found error'
#
#
# def _get_hit_count_and_clicks(url_conversion, campaign):
#     """
#     This returns the hit counts of URL conversion record and clicks of SMS campaign blast
#     from database table 'sms_campaign_blast'
#     :param url_conversion: URL conversion obj
#     :param campaign: SMS campaign obj
#     :type campaign: SmsCampaign
#     :return:
#     """
#     # Need to commit the session because Celery has its own session, and our session does not
#     # know about the changes that Celery session has made.
#     db.session.commit()
#     sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
#     return url_conversion.hit_count, sms_campaign_blasts.clicks
#
#
# def _get_args_from_url(url):
#     """
#     This gets the args from the signed URL
#     :param url:
#     :return:
#     """
#     args = url.split('?')[1].split('&')
#     request_args = dict()
#     for arg_pair in args:
#         key, value = arg_pair.split('=')
#         request_args[key] = value
#     request_args['signature'] = urllib.unquote(request_args['signature']).decode('utf8')
#     return request_args
#
#
# # TODO: remove this when app is up
# def _use_ngrok_or_local_address(url):
#     """
#     This hits the endpoint exposed via ngrok. If ngrok is not running, it changes the URL
#     to localhost and returns the GET response.
#     :param url:
#     :return:
#     """
#     response_get = requests.get(url)
#     if response_get.status_code == ResourceNotFound.http_status_code():
#         localhost_url = replace_ngrok_link_with_localhost(url)
#         response_get = requests.get(localhost_url)
#     return response_get
