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
import urllib
from datetime import datetime, timedelta

# Third Party
import requests

# Common Utils
from sms_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    get_candidates_of_smartlist
from sms_campaign_service.common.models.user import DomainRole
from sms_campaign_service.common.routes import SmsCampaignApiUrl, CandidateApiUrl
from sms_campaign_service.common.campaign_services.custom_errors import (CampaignException,
                                                                         EmptyDestinationUrl)
from sms_campaign_service.common.error_handling import (ResourceNotFound, InternalServerError,
                                                        InvalidUsage)
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from sms_campaign_service.common.campaign_services.validators import \
    validate_blast_candidate_url_conversion_in_db
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


# Database Models
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.models.sms_campaign import SmsCampaign, SmsCampaignBlast
from sms_campaign_service.common.models.misc import (UrlConversion, Frequency, Activity)

# Service Specific
from sms_campaign_service.sms_campaign_app import app
from sms_campaign_service.common.utils.datetime_utils import DatetimeUtils
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.common.utils.handy_functions import add_role_to_test_user
from sms_campaign_service.modules.handy_functions import replace_ngrok_link_with_localhost
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.tests.modules.common_functions import \
    (assert_on_blasts_sends_url_conversion_and_activity, assert_for_activity,
     assert_api_send_response, assert_campaign_schedule, delete_test_scheduled_task)


# TODO: Add a test where two smartlists have same candidate associated with them.
# TODO: Sends should be 1 not 2.
class TestCeleryTasks(object):
    """
    This class contains tasks that run on celery or if  the fixture they use has some
    processing on Celery.
    """

    @staticmethod
    def send_campaign(campaign, access_token):
        """
        This is a helper method used to send a given SMS campaign.
        """
        response_send = CampaignsTestsHelpers.send_campaign(SmsCampaignApiUrl.SEND, campaign,
                                                            access_token,
                                                            blasts_url=SmsCampaignApiUrl.BLASTS)
        return response_send

    def test_campaign_send_with_two_candidates_with_different_phones_multiple_links_in_text(
            self, access_token_first, user_first, sms_campaign_of_current_user):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates. Body text of SMS campaign has multiple URLs
        present.
        """
        campaign_id = sms_campaign_of_current_user['id']
        campaign = SmsCampaign.get_by_id(str(campaign_id))
        campaign.update(body_text='Hi all, please visit http://www.abc.com or '
                                  'http://www.123.com or http://www.xyz.com')
        response_send = self.send_campaign(campaign, access_token_first)
        assert_api_send_response(campaign, response_send, requests.codes.OK)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2, campaign_id,
                                                           access_token_first)

    def test_campaign_send_with_two_candidates_with_one_phone(
            self, access_token_first, user_first, sms_campaign_with_one_valid_candidate):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate has no phone number associated. So, total sends should be 1.
        """
        response_send = self.send_campaign(sms_campaign_with_one_valid_candidate,
                                           access_token_first)
        assert_api_send_response(sms_campaign_with_one_valid_candidate, response_send,
                                 requests.codes.OK)
        assert_on_blasts_sends_url_conversion_and_activity(
            user_first.id, 1, sms_campaign_with_one_valid_candidate['id'], access_token_first)

    def test_campaign_send_with_two_candidates_having_different_phones_one_link_in_text(
            self, access_token_first, user_first, sms_campaign_of_current_user):
        """
        User auth token is valid, campaign has one smartlist associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates.
        """
        campaign_id = sms_campaign_of_current_user['id']
        response_send = self.send_campaign(sms_campaign_of_current_user, access_token_first)
        assert_api_send_response(sms_campaign_of_current_user, response_send, requests.codes.OK)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2, campaign_id,
                                                           access_token_first)

    def test_campaign_send_with_two_candidates_with_different_phones_no_link_in_text(
            self, access_token_first, user_first, sms_campaign_of_current_user):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. Both candidates have different phone numbers associated. SMS Campaign
        should be sent to both of the candidates. Body text of SMS campaign has no URL link
        present.
        """
        campaign_id = sms_campaign_of_current_user['id']
        campaign = SmsCampaign.get_by_id(str(campaign_id))
        campaign.update(body_text='Hi,all')
        response_send = self.send_campaign(sms_campaign_of_current_user, access_token_first)
        assert_api_send_response(campaign, response_send, requests.codes.OK)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2, campaign_id,
                                                           access_token_first)

    def test_campaign_send_with_multiple_smartlists(
            self, access_token_first, user_first, sms_campaign_with_two_smartlists):
        """
        - This tests the endpoint /v1/sms-campaigns/:id/send

        User auth token is valid, campaign has one smart list associated. Both smartlists have one
        candidate associated. Total number of sends should be 2.
        """
        campaign_id = sms_campaign_with_two_smartlists['id']
        response_post = self.send_campaign(sms_campaign_with_two_smartlists, access_token_first)
        assert_api_send_response(sms_campaign_with_two_smartlists, response_post, requests.codes.OK)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2, campaign_id,
                                                           access_token_first)

    def test_campaign_send_with_same_candidate_in_multiple_smartlists(
            self, access_token_first, user_first,
            sms_campaign_with_same_candidate_in_multiple_smartlists):
        """
        - This tests the endpoint /v1/sms-campaigns/:id/send

        User auth token is valid, campaign has two smartlists associated, Smartlists have one
        common candidate. One smartlist has 2 candidate and other smartlist has 1 candidates.
        Total number of sends should be 2.
        """
        campaign_id = sms_campaign_with_same_candidate_in_multiple_smartlists['id']
        response_post = self.send_campaign(sms_campaign_with_same_candidate_in_multiple_smartlists,
                                           access_token_first)
        assert_api_send_response(sms_campaign_with_same_candidate_in_multiple_smartlists,
                                 response_post, requests.codes.OK)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2, campaign_id,
                                                           access_token_first)

# TODO: Assigned a JIRA GET-1277 to saad for these
# class TestCampaignSchedule(object):
#     """
#     This is the test for scheduling a campaign ans verify it is sent to candidate as
#     per send time.
#     """
#
#     def test_one_time_campaign_schedule_and_validate_task_run(
#             self, headers, user_first, access_token_first, sms_campaign_of_current_user):
#         """
#         Here we schedule SMS campaign one time with all valid parameters. Then we check
#         that task is run fine and assert the blast, sends and activity have been created
#         in database.
#         """
#         data = generate_campaign_schedule_data()
#         data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(seconds=5))
#         response = requests.post(
#             SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user['id'],
#             headers=headers, data=json.dumps(data))
#         task_id = assert_campaign_schedule(response, user_first.id,
#                                            sms_campaign_of_current_user['id'])
#         CampaignsTestsHelpers.get_blasts_with_polling(
#             sms_campaign_of_current_user, access_token_first,
#             blasts_url=SmsCampaignApiUrl.BLASTS % sms_campaign_of_current_user['id'], timeout=30)
#         assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2,
#                                                            sms_campaign_of_current_user['id'],
#                                                            access_token_first,
#                                                            blast_timeout=60)
#         delete_test_scheduled_task(task_id, headers)
#
#     def test_periodic_campaign_schedule_and_validate_run(self, headers, user_first,
#                                                          access_token_first,
#                                                          sms_campaign_of_current_user):
#         """
#         This is test to schedule SMS campaign with all valid parameters. This should get OK
#         response.
#         """
#         data = generate_campaign_schedule_data().copy()
#         data['frequency_id'] = Frequency.CUSTOM
#         data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(seconds=5))
#         response = requests.post(
#             SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user['id'],
#             headers=headers, data=json.dumps(data))
#         task_id = assert_campaign_schedule(response, user_first.id,
#                                            sms_campaign_of_current_user['id'])
#         # assert that scheduler has sent the campaign for the first time
#         assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2,
#                                                            sms_campaign_of_current_user['id'],
#                                                            access_token_first,
#                                                            blast_timeout=60)
#
#         # assert that scheduler has sent the campaign for the second time
#         assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2,
#                                                            sms_campaign_of_current_user['id'],
#                                                            access_token_first,
#                                                            expected_blasts=2,
#                                                            blast_index=1, blast_timeout=60)
#         delete_test_scheduled_task(task_id, headers)
#
#     def test_campaign_daily_schedule_and_validate_task_run(
#             self, headers, user_first, access_token_first, sms_campaign_of_current_user):
#         """
#         Here we schedule SMS campaign on daily basis. Then we check whether that task runs fine
#         and assert the blast, sends and activity have been created in database. It should run only
#         once during tests.
#         """
#         data = generate_campaign_schedule_data()
#         data['frequency_id'] = Frequency.DAILY
#         data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(seconds=5))
#         response = requests.post(SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user['id'],
#                                  headers=headers, data=json.dumps(data))
#         task_id = assert_campaign_schedule(response, user_first.id, sms_campaign_of_current_user['id'])
#         assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 2,
#                                                            sms_campaign_of_current_user['id'],
#                                                            access_token_first)
#         delete_test_scheduled_task(task_id, headers)


class TestURLRedirectionApi(object):
    """
    This class contains tests for endpoint /v1/redirect/:id
    As response from Api endpoint is returned to candidate. So ,in case of any error,
    candidate should only get internal server error.
    """

    def test_for_get(self, user_first,
                     url_conversion_by_send_test_sms_campaign,
                     sms_campaign_of_current_user):
        """
        GET method should give OK response. We check the "hit_count" and "clicks" before
        hitting the endpoint and after hitting the endpoint. Then we assert that both
        "hit_count" and "clicks" have been successfully updated by '1' in database.
        """
        # stats before making HTTP GET request to source URL
        campaign_in_db = SmsCampaign.get_by_id(sms_campaign_of_current_user['id'])
        hit_count, clicks = _get_hit_count_and_clicks(url_conversion_by_send_test_sms_campaign,
                                                      campaign_in_db)
        response_get = _use_ngrok_or_local_address(
            'get', url_conversion_by_send_test_sms_campaign.source_url)
        assert response_get.status_code == requests.codes.OK, 'Response should be ok'
        # stats after making HTTP GET request to source URL
        hit_count_after, clicks_after = _get_hit_count_and_clicks(
            url_conversion_by_send_test_sms_campaign,
            campaign_in_db)
        assert hit_count_after == hit_count + 1
        assert clicks_after == clicks + 1
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_SMS_CLICK,
                            campaign_in_db.id)

    def test_get_with_no_signature(self, url_conversion_by_send_test_sms_campaign):
        """
        Removing signature of signed redirect URL. It should get internal server error.
        """
        url_excluding_signature = \
            url_conversion_by_send_test_sms_campaign.source_url.split('?')[0]
        request_and_assert_internal_server_error(url_excluding_signature)

    def test_get_with_empty_destination_url(self, url_conversion_by_send_test_sms_campaign):
        """
        Making destination URL an empty string here, it should get internal server error.
        """
        # forcing destination URL to be empty
        _make_destination_url_empty(url_conversion_by_send_test_sms_campaign)
        request_and_assert_internal_server_error(
            url_conversion_by_send_test_sms_campaign.source_url)

    def test_get_with_deleted_campaign(
            self, headers, sms_campaign_of_current_user,
            url_conversion_by_send_test_sms_campaign):
        """
        Here we first delete the campaign, and then test functionality of url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should result in
        ResourceNotFound Error. But candidate should get Internal server error. Hence this test
        should get internal server error.
        """
        _delete_sms_campaign(sms_campaign_of_current_user, headers)
        request_and_assert_internal_server_error(
            url_conversion_by_send_test_sms_campaign.source_url)

    def test_get_with_deleted_candidate(self, url_conversion_by_send_test_sms_campaign,
                                        headers, access_token_first,
                                        sms_campaign_of_current_user, user_first):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should get ResourceNotFound Error.
        But candidate should only get internal server error. So this test asserts we get internal
        server error.
        """
        [smartlist_id] = sms_campaign_of_current_user['list_ids']
        candidates = get_candidates_of_smartlist(smartlist_id, True, access_token_first)
        candidate_ids = [candidate_id for candidate_id in candidates]
        for candidate_id in candidate_ids:
            _delete_candidate(candidate_id, headers, user_first)
        request_and_assert_internal_server_error(url_conversion_by_send_test_sms_campaign.source_url)

    def test_get_with_deleted_url_conversion(self, url_conversion_by_send_test_sms_campaign):
        """
        Here we first delete the url_conversion object. which internally deletes the
        sms_campaign_send record as it uses url_conversion as primary key. We then test
        functionality of url_redirect by making HTTP GET call to endpoint /v1/redirect.
        It should get ResourceNotFound Error. But candidate should only get internal server error.
        So this test asserts we get internal server error.
        """
        source_url = url_conversion_by_send_test_sms_campaign.source_url
        _delete_url_conversion(url_conversion_by_send_test_sms_campaign)
        request_and_assert_internal_server_error(source_url)


class TestURLRedirectionMethods(object):
    """
    This class contains tests for the methods that are used in case of URL redirection.

    """

    def test_process_url_redirect_empty_destination_url(self,
                                                        url_conversion_by_send_test_sms_campaign):
        """
        Here we are testing the functionality of url_redirect() class method of
        CampaignBase by setting destination URL an empty string. It should get custom exception
        EmptyDestinationUrl.
        """
        _make_destination_url_empty(url_conversion_by_send_test_sms_campaign)
        try:
            _call_process_url_redirect(url_conversion_by_send_test_sms_campaign)
            assert None, 'EmptyDestinationUrl custom exception should be raised'
        except EmptyDestinationUrl as error:
            assert error.error_code == CampaignException.EMPTY_DESTINATION_URL

    def test_process_url_redirect_with_deleted_campaign(
            self, headers, sms_campaign_of_current_user,
            url_conversion_by_send_test_sms_campaign):
        """
        Here we first delete the campaign which internally deletes campaign send record,
        and then test functionality of url_redirect. It should result in ResourceNotFound Error.
        """
        _delete_sms_campaign(sms_campaign_of_current_user, headers)
        _assert_for_no_campaign_send_obj(url_conversion_by_send_test_sms_campaign)

    def test_process_url_redirect_with_deleted_candidate(self, headers,sms_campaign_of_current_user,
                                                         url_conversion_by_send_test_sms_campaign,
                                                         access_token_first, user_first):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of url_redirect().
        It should get ResourceNotFound Error.
        """
        [smartlist_id] = sms_campaign_of_current_user['list_ids']
        candidates = get_candidates_of_smartlist(smartlist_id, True, access_token_first)
        candidate_ids = [candidate_id for candidate_id in candidates]
        for candidate_id in candidate_ids:
            _delete_candidate(candidate_id, headers, user_first)
        try:
            _call_process_url_redirect(url_conversion_by_send_test_sms_campaign)
        except ResourceNotFound as error:
            assert error.status_code == ResourceNotFound.http_status_code()

    def test_process_url_redirect_with_deleted_url_conversion(
            self, url_conversion_by_send_test_sms_campaign):
        """
        Here we first delete the url_conversion object. which internally deletes the
        sms_campaign_send record as it uses url_conversion as primary key. We then test
        functionality of url_redirect(). It should get ResourceNotFound Error.
        """
        _delete_url_conversion(url_conversion_by_send_test_sms_campaign)
        _assert_for_no_campaign_send_obj(url_conversion_by_send_test_sms_campaign)

    def test_validate_blast_candidate_url_conversion_in_db_with_no_candidate(
            self, sent_campaign_and_blast_ids,
            url_conversion_by_send_test_sms_campaign):
        """
        Here we pass None candidate, and then test functionality of
        validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
        it should result in ResourceNotFound Error.
        """
        _, blast_ids = sent_campaign_and_blast_ids
        blast_obj = SmsCampaignBlast.get(blast_ids[0])
        _test_validate_blast_candidate_url_conversion_in_db(
            blast_obj, None, url_conversion_by_send_test_sms_campaign)

    def test_validate_blast_candidate_url_conversion_in_db_with_no_blast(
            self, candidate_first, url_conversion_by_send_test_sms_campaign):
        """
        Here we pass blast as None, and then test functionality of
        validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
        It should result in ResourceNotFound Error.
        """
        _test_validate_blast_candidate_url_conversion_in_db(
            None, candidate_first, url_conversion_by_send_test_sms_campaign)

    def test_validate_blast_candidate_url_conversion_in_db_with_no_url_conversion(
            self, candidate_first, sent_campaign_and_blast_ids):
        """
        Here we pass url_conversion obj  as None, and then test functionality of
        validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
        It should result in ResourceNotFound Error.
        """
        _, blast_ids = sent_campaign_and_blast_ids
        blast_obj = SmsCampaignBlast.get(blast_ids[0])
        _test_validate_blast_candidate_url_conversion_in_db(
            blast_obj, candidate_first, None)

    def test_pre_process_url_redirect_with_empty_data(self):
        """
        This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
        All parameters passed are None, So, it should result in Invalid Usage Error.
        """
        try:
            CampaignBase.pre_process_url_redirect({}, None)
        except InvalidUsage as error:
            assert error.status_code == InvalidUsage.http_status_code()

    def test_pre_process_url_redirect_with_valid_data(self,
                                                      url_conversion_by_send_test_sms_campaign):
        """
        This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
        All parameters passed are valid, So, it should not get any error.
        """
        request_args = _get_args_from_url(url_conversion_by_send_test_sms_campaign.source_url)
        _call_pre_process_url_redirect(request_args,
                                       url_conversion_by_send_test_sms_campaign.source_url)

    def test_pre_process_url_redirect_with_missing_key_signature(
            self, url_conversion_by_send_test_sms_campaign):
        """
        This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
        signature is missing from request_arg.So, it should get Invalid Usage Error.
        """
        try:
            request_args = _get_args_from_url(url_conversion_by_send_test_sms_campaign.source_url)
            del request_args['signature']
            _call_pre_process_url_redirect(request_args,
                                           url_conversion_by_send_test_sms_campaign.source_url)
        except InvalidUsage as error:
            assert error.status_code == InvalidUsage.http_status_code()


def _delete_sms_campaign(campaign, header):
    """
    This calls the API /campaigns/:id to delete the given campaign
    :param campaign:
    :param header:
    :return:
    """
    campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
    response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % campaign_id, headers=header)
    assert response.status_code == requests.codes.OK, 'It should get ok response (200)'
    db.session.commit()


def request_and_assert_internal_server_error(url):
    """
    This makes HTTP GET call on given URL and assert that it receives internal server error.
    """
    response_get = _use_ngrok_or_local_address('get', url)
    assert response_get.status_code == InternalServerError.http_status_code(), \
        'It should get Internal server error'


def _delete_candidate(candidate_id, headers, user):
    """
    This deletes the given candidate from candidate_service API.
    """
    try:
        add_role_to_test_user(user, [DomainRole.Roles.CAN_DELETE_CANDIDATES])
    except InvalidUsage:
        pass  # Maybe roll has been assigned already to given user
    response = requests.delete(CandidateApiUrl.CANDIDATE % candidate_id, headers=headers)
    assert response.status_code == 204
    db.session.commit()


def _delete_url_conversion(url_conversion_obj):
    """
    This deletes the candidate of given id
    :param url_conversion_obj:
    """
    UrlConversion.delete(url_conversion_obj)


def _test_validate_blast_candidate_url_conversion_in_db(blast, candidate, url_conversion_obj):
    """
    This tests the functionality of validate_blast_candidate_url_conversion_in_db() method in
        campaign_utils.py.
    """
    try:
        validate_blast_candidate_url_conversion_in_db(blast, candidate, url_conversion_obj)
        assert None, 'It should get resource not found error'
    except ResourceNotFound as error:
        assert error.status_code == ResourceNotFound.http_status_code(), \
            'It should get Resource not found error'


def _get_hit_count_and_clicks(url_conversion, campaign):
    """
    This returns the hit counts of URL conversion record and clicks of SMS campaign blast
    from database table 'sms_campaign_blast'
    :param url_conversion: URL conversion obj
    :param campaign: SMS campaign obj
    :type campaign: SmsCampaign
    """
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    sms_campaign_blasts = campaign.blasts[0]
    return url_conversion.hit_count, sms_campaign_blasts.clicks


def _get_args_from_url(url):
    """
    This gets the args from the signed URL
    """
    args = url.split('?')[1].split('&')
    request_args = dict()
    for arg_pair in args:
        key, value = arg_pair.split('=')
        request_args[key] = value
    request_args['signature'] = urllib.unquote(request_args['signature']).decode('utf8')
    return request_args


def _call_process_url_redirect(url_conversion_obj):
    """
    This directly calls the url_redirect() class method of CampaignBase
    """
    with app.app_context():
        CampaignBase.url_redirect(url_conversion_obj.id, CampaignUtils.SMS)


def _call_pre_process_url_redirect(request_args, url):
    """
    This directly calls the pre_process_url_redirect() class method of CampaignBase
    """
    with app.app_context():
        SmsCampaignBase.pre_process_url_redirect(request_args, url)


def _make_destination_url_empty(url_conversion_obj):
    """
    Here we make the destination URL an empty string.
    """
    url_conversion_obj.update(destination_url='')


def _assert_for_no_campaign_send_obj(url_conversion_obj):
    """
    This asserts the functionality of url_redirect() by deleting campaign from
    database.
    """
    try:
        _call_process_url_redirect(url_conversion_obj)
        assert None, 'ResourceNotFound exception should be raised'
    except ResourceNotFound as error:
        assert str(url_conversion_obj.id) in error.message


# TODO: remove this when app is up
def _use_ngrok_or_local_address(method, url):
    """
    This hits the endpoint exposed via ngrok. If ngrok is not running, it changes the URL
    to localhost and returns the response of HTTP request.
    :param url:
    :return:
    """
    request_method = getattr(requests, method)
    response = request_method(url)
    if response.status_code == ResourceNotFound.http_status_code():
        localhost_url = replace_ngrok_link_with_localhost(url)
        response = request_method(localhost_url)
    return response
