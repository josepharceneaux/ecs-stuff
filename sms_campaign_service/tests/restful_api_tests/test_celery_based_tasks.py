# """
# Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>
#
#     This module contains pyTests of tasks that run on Celery. These tests are put in
#     separate file such that these tests run at the end of all tests because they needed to
#     add time.sleep() due to background processing of Celery.
#
#
#     This module also contains pyTests for endpoint
#
#                 /v1/campaigns/:id/redirect/:id?candidate_id=id
#
#     of SMS Campaign APP.
# """
#
# # Standard Library
# import time
#
# # Third Party
# import requests
#
# # Common Utils
# from sms_campaign_service.common.routes import SmsCampaignApiUrl
# from sms_campaign_service.common.utils.activity_utils import ActivityMessageIds
# from sms_campaign_service.common.error_handling import (ResourceNotFound,
#                                                         InternalServerError,
#                                                         MethodNotAllowed)
# # Database Models
# from sms_campaign_service.common.models.misc import UrlConversion
# from sms_campaign_service.common.models.candidate import Candidate
# from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)
#
# # Service Specific
# from sms_campaign_service import db
# from sms_campaign_service.sms_campaign_base import SmsCampaignBase
# from sms_campaign_service.custom_exceptions import SmsCampaignApiException
# from sms_campaign_service.utilities import replace_ngrok_link_with_localhost
# from sms_campaign_service.tests.modules.common_functions import \
#     (assert_on_blasts_sends_url_conversion_and_activity, assert_for_activity, get_reply_text)
#
# # TODO: debug why Celery tasks fail sometime
# SLEEP_TIME = 25  # due to background processing of tasks (Celery)
# OFFSET = 20  # due to background processing of tasks (Celery)
# ADDITIONAL_OFFSET = 0  # due to background processing of tasks (Celery)
#
#
# class TestCeleryTasks(object):
#     """
#     This class contains tasks that run on celery or if  the fixture they use has some
#     processing on Celery.
#     """
#
#     def test_post_with_valid_token_one_smartlist_two_candidates_with_different_phones_multiple_links_in_text(
#             self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
#             sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
#         """
#         User auth token is valid, campaign has one smart list associated. Smartlist has two
#         candidates. Both candidates have different phone numbers associated. SMS Campaign
#         should be sent to both of the candidates. Body text of SMS campaign has multiple URLs
#         present.
#         :return:
#         """
#         campaign = SmsCampaign.get_by_id(str(sms_campaign_of_current_user.id))
#         campaign.update(body_text='Hi,all please visit http://www.abc.com or '
#                                   'http://www.123.com or http://www.xyz.com')
#         response_post = requests.post(
#             SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS_URL % sms_campaign_of_current_user.id,
#             headers=dict(Authorization='Bearer %s' % auth_token))
#         assert response_post.status_code == 200, 'Response should be ok (200)'
#         assert response_post.json()['total_sends'] == 2
#         assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
#         # Need to add this as processing of POST request runs on celery
#         time.sleep(SLEEP_TIME + OFFSET + ADDITIONAL_OFFSET)
#         assert_on_blasts_sends_url_conversion_and_activity(sample_user.id, response_post,
#                                                            str(sms_campaign_of_current_user.id))
#
#     def test_post_with_valid_token_one_smartlist_two_candidates_with_one_phone(
#             self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
#             sample_sms_campaign_candidates, candidate_phone_1):
#         """
#         User auth token is valid, campaign has one smart list associated. Smartlist has two
#         candidates. One candidate have no phone number associated. So, total sends should be 1.
#         :return:
#         """
#         response_post = requests.post(
#             SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS_URL % sms_campaign_of_current_user.id,
#             headers=dict(Authorization='Bearer %s' % auth_token))
#         assert response_post.status_code == 200, 'Response should be ok (200)'
#         assert response_post.json()['total_sends'] == 1
#         assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
#         time.sleep(SLEEP_TIME + OFFSET)
#         assert_on_blasts_sends_url_conversion_and_activity(sample_user.id, response_post,
#                                                            str(sms_campaign_of_current_user.id))
#
#     def test_post_with_valid_token_one_smartlist_two_candidates_with_different_phones_one_link_in_text(
#             self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
#             sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
#         """
#         User auth token is valid, campaign has one smartlist associated. Smartlist has two
#         candidates. Both candidates have different phone numbers associated. SMS Campaign
#         should be sent to both of the candidates.
#         :return:
#         """
#         response_post = requests.post(
#             SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS_URL % sms_campaign_of_current_user.id,
#             headers=dict(Authorization='Bearer %s' % auth_token))
#         assert response_post.status_code == 200, 'Response should be ok (200)'
#         assert response_post.json()['total_sends'] == 2
#         assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
#         time.sleep(SLEEP_TIME + OFFSET)  # Need to add this as processing of POST
#         # request runs on celery
#         assert_on_blasts_sends_url_conversion_and_activity(sample_user.id,
#                                                            response_post,
#                                                            str(sms_campaign_of_current_user.id))
#
#     def test_post_with_valid_token_one_smartlist_two_candidates_with_different_phones_no_link_in_text(
#             self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
#             sample_sms_campaign_candidates, candidate_phone_1, candidate_phone_2):
#         """
#         User auth token is valid, campaign has one smart list associated. Smartlist has two
#         candidates. Both candidates have different phone numbers associated. SMS Campaign
#         should be sent to both of the candidates. Body text of SMS campaign has no URL link
#         present.
#         :return:
#         """
#         campaign = SmsCampaign.get_by_id(str(sms_campaign_of_current_user.id))
#         campaign.update(body_text='Hi,all')
#         response_post = requests.post(
#             SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS_URL % sms_campaign_of_current_user.id,
#             headers=dict(Authorization='Bearer %s' % auth_token))
#         assert response_post.status_code == 200, 'Response should be ok (200)'
#         assert response_post.json()['total_sends'] == 2
#         assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
#         # Need to add this as processing of POST request runs on celery
#         time.sleep(SLEEP_TIME + OFFSET)
#         assert_on_blasts_sends_url_conversion_and_activity(sample_user.id,
#                                                            response_post,
#                                                            str(sms_campaign_of_current_user.id))
#
#     def test_post_with_valid_data_with_campaign_sent(self, user_phone_1,
#                                                      sms_campaign_of_current_user,
#                                                      candidate_phone_1,
#                                                      process_send_sms_campaign):
#         """
#         - This tests the endpoint /receive
#
#         Here we make HTTP POST  request with no data, Response should be OK as this response
#         is returned to Twilio API.
#         Candidate is associated with an SMS campaign. Then we assert that reply has been saved
#         and replies count has been incremented by 1. Finally we assert that activity has been
#         created in database table 'Activity'
#         :return:
#         """
#         reply_text = "What's the venue?"
#         reply_count_before = get_replies_count(sms_campaign_of_current_user)
#         response_get = requests.post(SmsCampaignApiUrl.RECEIVE_URL,
#                                      data={'To': user_phone_1.value,
#                                            'From': candidate_phone_1.value,
#                                            'Body': reply_text})
#         assert response_get.status_code == 200, 'Response should be ok'
#         assert 'xml' in str(response_get.text).strip()
#         time.sleep(SLEEP_TIME)  # Need to add this as processing of POST request runs on celery
#         campaign_reply_in_db = get_reply_text(candidate_phone_1)
#         assert campaign_reply_in_db.body_text == reply_text
#         reply_count_after = get_replies_count(sms_campaign_of_current_user)
#         assert reply_count_after == reply_count_before + 1
#         assert_for_activity(user_phone_1.user_id, ActivityMessageIds.CAMPAIGN_SMS_REPLY,
#                             campaign_reply_in_db.id)
#
#     def test_post_with_valid_token_and_multiple_smartlists(
#             self, auth_token, sample_user, sms_campaign_of_current_user, sms_campaign_smartlist,
#             sms_campaign_smartlist_2, sample_sms_campaign_candidates, candidate_phone_1):
#         """
#         - This tests the endpoint /v1/campaigns/:id/send
#
#         User auth token is valid, campaign has one smart list associated. Smartlist has two
#         candidates. One candidate have no phone number associated. So, total sends should be 1.
#         :return:
#         """
#         response_post = requests.post(
#             SmsCampaignApiUrl.CAMPAIGN_SEND_PROCESS_URL % sms_campaign_of_current_user.id,
#             headers=dict(Authorization='Bearer %s' % auth_token))
#         assert response_post.status_code == 200, 'Response should be ok (200)'
#         assert response_post.json()['total_sends'] == 1
#         assert str(sms_campaign_of_current_user.id) in response_post.json()['message']
#         time.sleep(SLEEP_TIME)  # Need to add this as processing of POST request runs on celery
#         assert_on_blasts_sends_url_conversion_and_activity(sample_user.id,
#                                                            response_post,
#                                                            str(sms_campaign_of_current_user.id))
#
#
# def get_replies_count(campaign):
#     """
#     This returns the replies counts of SMS campaign from database table 'sms_campaign_blast'
#     :param campaign: SMS campaign obj
#     :return:
#     """
#     db.session.commit()
#     sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
#     return sms_campaign_blasts.replies
#
#
# class TestSmsCampaignURLRedirection(object):
#     """
#     This class contains tests for endpoint /v1/campaigns/:id/redirect/:id?candidate_id=id.
#     """
#
#     def test_for_post(self, url_conversion_by_send_test_sms_campaign):
#         """
#         POST method should not be allowed at this endpoint.
#         :return:
#         """
#
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
#     def test_endpoint_for_get(self, sample_user,
#                               url_conversion_by_send_test_sms_campaign,
#                               sms_campaign_of_current_user):
#         """
#         GET method should give OK response. We check the "hit_count" and "clicks" before
#         hitting the endpoint and after hitting the endpoint. Then we assert that both
#         "hit_count" and "clicks" have been successfully updated by '1' in database.
#         :return:
#         """
#         # stats before making HTTP GET request to source URL
#         hit_count, clicks = _get_hit_count_and_clicks(url_conversion_by_send_test_sms_campaign,
#                                                       sms_campaign_of_current_user)
#         response_get = requests.get(url_conversion_by_send_test_sms_campaign.source_url)
#         # TODO: remove this when app is up
#         if response_get.status_code == ResourceNotFound.http_status_code():
#             localhost_url = replace_ngrok_link_with_localhost(
#                 url_conversion_by_send_test_sms_campaign.source_url)
#             response_get = requests.get(localhost_url)
#
#         assert response_get.status_code == 200, 'Response should be ok'
#         # stats after making HTTP GET request to source URL
#         hit_count_after, clicks_after = _get_hit_count_and_clicks(
#             url_conversion_by_send_test_sms_campaign,
#             sms_campaign_of_current_user)
#         assert hit_count_after == hit_count + 1
#         assert clicks_after == clicks + 1
#         assert_for_activity(sample_user.id, ActivityMessageIds.CAMPAIGN_SMS_CLICK,
#                             sms_campaign_of_current_user.id)
#
#     def test_endpoint_for_get_with_no_candidate_id(self, url_conversion_by_send_test_sms_campaign):
#         """
#         Removing candidate id from destination URL. It should get internal server error.
#         :return:
#         """
#         url_excluding_candidate_id = \
#             url_conversion_by_send_test_sms_campaign.source_url.split('?')[0]
#         response_get = requests.get(url_excluding_candidate_id)
#         # TODO: remove this when app is up
#         if response_get.status_code == ResourceNotFound.http_status_code():
#             localhost_url = replace_ngrok_link_with_localhost(url_excluding_candidate_id)
#             response_get = requests.get(localhost_url)
#
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get internal server error'
#
#     def test_endpoint_for_get_with_empty_destination_url(self,
#                                                          url_conversion_by_send_test_sms_campaign):
#         """
#         Making destination URL an empty string here, it should get internal server error.
#         :return:
#         """
#         # forcing destination URL to be empty
#         url_conversion_by_send_test_sms_campaign.update(destination_url='')
#         response_get = requests.get(url_conversion_by_send_test_sms_campaign.source_url)
#         # TODO: remove this when app is up
#         if response_get.status_code == ResourceNotFound.http_status_code():
#             localhost_url = replace_ngrok_link_with_localhost(
#                 url_conversion_by_send_test_sms_campaign.source_url)
#             response_get = requests.get(localhost_url)
#
#         assert response_get.status_code == InternalServerError.http_status_code(), \
#             'It should get internal server error'
#
#     def test_method_pre_process_url_redirect_with_None_data(self):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of SmsCampaignBase.
#         All parameters passed are None, So, it should raise MissingRequiredField Error.
#         :return:
#         """
#         try:
#             SmsCampaignBase.pre_process_url_redirect(None, None, None)
#         except Exception as error:
#             assert error.error_code == SmsCampaignApiException.MISSING_REQUIRED_FIELD
#             assert 'candidate_id' in error.message
#             assert 'campaign_id' in error.message
#             assert 'url_conversion_id' in error.message
#
#     def test_method_pre_process_url_redirect_with_valid_data(self,
#                                                              sms_campaign_of_current_user,
#                                                              url_conversion_by_send_test_sms_campaign,
#                                                              candidate_first):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of SmsCampaignBase.
#         All parameters passed are valid, So, it should get OK response.
#         :param sms_campaign_of_current_user:
#         :param url_conversion_by_send_test_sms_campaign:
#         :param candidate_first:
#         :return:
#         """
#         candidate = None
#         campaign = None
#         try:
#             campaign, url_conversion, candidate = SmsCampaignBase.pre_process_url_redirect(
#                 sms_campaign_of_current_user.id,
#                 url_conversion_by_send_test_sms_campaign.id,
#                 candidate_first.id)
#
#         except Exception:
#             pass
#         assert candidate
#         assert campaign
#
#     def test_method_pre_process_url_redirect_with_deleted_campaign(self, valid_header,
#                                                                    sms_campaign_of_current_user,
#                                                                    url_conversion_by_send_test_sms_campaign,
#                                                                    candidate_first):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of SmsCampaignBase.
#         Here we first delete the campaign, and then test functionality of pre_process_url_redirect
#         class method of SmsCampaignBase. It should give ResourceNotFound Error.
#         """
#         campaing_id = sms_campaign_of_current_user.id
#         _delete_sms_campaign(sms_campaign_of_current_user, valid_header)
#         try:
#             SmsCampaignBase.pre_process_url_redirect(campaing_id,
#                                                      url_conversion_by_send_test_sms_campaign.id,
#                                                      candidate_first.id)
#
#         except Exception as error:
#             assert error.status_code == ResourceNotFound.http_status_code()
#             str(campaing_id) in error.message
#
#     def test_method_pre_process_url_redirect_with_deleted_candidate(self,
#                                                                     sms_campaign_of_current_user,
#                                                                     url_conversion_by_send_test_sms_campaign,
#                                                                     candidate_first):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of SmsCampaignBase.
#         Here we first delete the candidate, and then test functionality of pre_process_url_redirect
#         class method of SmsCampaignBase. It should give ResourceNotFound Error.
#         """
#         Candidate.delete(candidate_first)
#         try:
#             SmsCampaignBase.pre_process_url_redirect(sms_campaign_of_current_user.id,
#                                                      url_conversion_by_send_test_sms_campaign.id,
#                                                      candidate_first.id)
#
#         except Exception as error:
#             assert error.status_code == ResourceNotFound.http_status_code()
#             assert str(candidate_first.id) in error.message
#
#     def test_method_pre_process_url_redirect_with_deleted_url_conversion(self,
#                                                                          sms_campaign_of_current_user,
#                                                                          url_conversion_by_send_test_sms_campaign,
#                                                                          candidate_first):
#         """
#         This tests the functionality of pre_process_url_redirect() class method of SmsCampaignBase.
#         Here we first delete the url_conversion db record, and then test functionality of
#         pre_process_url_redirect class method of SmsCampaignBase.
#         It should give ResourceNotFound Error.
#         """
#         url_conversion_id = str(url_conversion_by_send_test_sms_campaign.id)
#         UrlConversion.delete(url_conversion_by_send_test_sms_campaign)
#         try:
#             SmsCampaignBase.pre_process_url_redirect(sms_campaign_of_current_user.id,
#                                                      url_conversion_by_send_test_sms_campaign.id,
#                                                      candidate_first.id)
#
#         except Exception as error:
#             assert error.status_code == ResourceNotFound.http_status_code()
#             assert url_conversion_id in error.message
#
#     def test_method_pre_process_url_redirect_with_empty_destination_url(
#             self, sample_user, sms_campaign_of_current_user,
#             url_conversion_by_send_test_sms_campaign,
#             candidate_first):
#         """
#         Making destination URL an empty string here, it should get internal server error.
#         Custom error should be EmptyDestinationUrl.
#         :return:
#         """
#         # forcing destination URL to be empty
#         url_conversion_by_send_test_sms_campaign.update(destination_url='')
#         try:
#
#             campaign, url_conversion_record, candidate = \
#                 SmsCampaignBase.pre_process_url_redirect(sms_campaign_of_current_user.id,
#                                                          url_conversion_by_send_test_sms_campaign.id,
#                                                          candidate_first.id)
#             camp_obj = SmsCampaignBase(sample_user.id)
#             camp_obj.process_url_redirect(campaign, url_conversion_record, candidate)
#
#         except Exception as error:
#             assert error.error_code == SmsCampaignApiException.EMPTY_DESTINATION_URL
#
#
# def _delete_sms_campaign(campaign, header):
#     """
#     This calls the API /campaigns/:id to delete the given campaign
#     :param campaign:
#     :param header:
#     :return:
#     """
#     response = requests.delete(SmsCampaignApiUrl.CAMPAIGN_URL % campaign.id,
#                                headers=header)
#     assert response.status_code == 200, 'should get ok response (200)'
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
#     db.session.commit()
#     sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
#     return url_conversion.hit_count, sms_campaign_blasts.clicks
