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
from sms_campaign_service.common.models.user import DomainRole
from sms_campaign_service.common.routes import SmsCampaignApiUrl, CandidateApiUrl
from sms_campaign_service.common.campaign_services.custom_errors import (CampaignException,
                                                                         EmptyDestinationUrl)
from sms_campaign_service.common.error_handling import (ResourceNotFound, InternalServerError,
                                                        InvalidUsage)
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.campaign_services.campaign_utils import (to_utc_str,
                                                                          CampaignUtils)
from sms_campaign_service.common.campaign_services.validators import \
    validate_blast_candidate_url_conversion_in_db

# Database Models
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.models.misc import (UrlConversion, Frequency, Activity)

# Service Specific
from sms_campaign_service.common.utils.handy_functions import add_role_to_test_user
from sms_campaign_service.sms_campaign_app import app
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.modules.handy_functions import replace_ngrok_link_with_localhost
from sms_campaign_service.tests.conftest import generate_campaign_schedule_data
from sms_campaign_service.tests.modules.common_functions import \
    (assert_on_blasts_sends_url_conversion_and_activity, assert_for_activity,
     assert_api_send_response, assert_campaign_schedule, SLEEP_TIME, delete_test_scheduled_task)


class TestCeleryTasks(object):
    """
    This class contains tasks that run on celery or if  the fixture they use has some
    processing on Celery.
    """

    def test_campaign_send_with_two_candidates_with_different_phones_multiple_links_in_text(
            self, access_token_first, user_first, scheduled_sms_campaign_of_current_user,
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
        campaign.update(body_text='Hi all, please visit http://www.abc.com or '
                                  'http://www.123.com or http://www.xyz.com')
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            user_first.id, 2, scheduled_sms_campaign_of_current_user)

    def test_campaign_send_with_two_candidates_with_one_phone(
            self, access_token_first, user_first, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sample_sms_campaign_candidates, candidate_phone_1):
        """
        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate have no phone number associated. So, total sends should be 1.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            user_first.id, 1, scheduled_sms_campaign_of_current_user)

    def test_campaign_send_with_two_candidates_having_different_phones_one_link_in_text(
            self, access_token_first, user_first, scheduled_sms_campaign_of_current_user,
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
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            user_first.id, 2, scheduled_sms_campaign_of_current_user)

    def test_campaign_send_with_two_candidates_with_different_phones_no_link_in_text(
            self, access_token_first, user_first, scheduled_sms_campaign_of_current_user,
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
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            user_first.id, 2, scheduled_sms_campaign_of_current_user)

    def test_campaign_send_with_multiple_smartlists(
            self, access_token_first, user_first, scheduled_sms_campaign_of_current_user,
            sms_campaign_smartlist, sms_campaign_smartlist_2, sample_sms_campaign_candidates,
            candidate_phone_1):
        """
        - This tests the endpoint /v1/sms-campaigns/:id/send

        User auth token is valid, campaign has one smart list associated. Smartlist has two
        candidates. One candidate have no phone number associated. So, total sends should be 1.
        :return:
        """
        response_post = requests.post(
            SmsCampaignApiUrl.SEND % scheduled_sms_campaign_of_current_user.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        assert_api_send_response(scheduled_sms_campaign_of_current_user, response_post, 200)
        assert_on_blasts_sends_url_conversion_and_activity(
            user_first.id, 1, scheduled_sms_campaign_of_current_user)


class TestCampaignSchedule(object):
    """
    This is the test for scheduling a campaign ans verify it is sent to candidate as
    per send time.
    """

    def test_one_time_campaign_schedule_and_validate_task_run(
            self, valid_header, user_first, sms_campaign_of_current_user,
            smartlist_for_not_scheduled_campaign, sample_sms_campaign_candidates,
            candidate_phone_1):
        """
        Here we schedule SMS campaign one time with all valid parameters. Then we check
        that task is run fine and assert the blast, sends and activity have been created
        in database.
        """
        data = generate_campaign_schedule_data()
        data['start_datetime'] = to_utc_str(datetime.utcnow() + timedelta(seconds=5))
        response = requests.post(
            SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
            headers=valid_header, data=json.dumps(data))
        task_id = assert_campaign_schedule(response, user_first.id,
                                           sms_campaign_of_current_user.id)
        time.sleep(2 * SLEEP_TIME)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 1,
                                                           sms_campaign_of_current_user)
        delete_test_scheduled_task(task_id, valid_header)

    def test_periodic_campaign_schedule_and_validate_run(
            self, valid_header, user_first, sms_campaign_of_current_user,
            smartlist_for_not_scheduled_campaign, sample_sms_campaign_candidates,
            candidate_phone_1):
        """
        This is test to schedule SMS campaign with all valid parameters. This should get OK
         response
        """
        data = generate_campaign_schedule_data().copy()
        data['frequency_id'] = Frequency.CUSTOM
        data['start_datetime'] = to_utc_str(datetime.utcnow())
        response = requests.post(
            SmsCampaignApiUrl.SCHEDULE % sms_campaign_of_current_user.id,
            headers=valid_header, data=json.dumps(data))
        task_id = assert_campaign_schedule(response, user_first.id,
                                           sms_campaign_of_current_user.id)
        time.sleep(SLEEP_TIME)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 1,
                                                           sms_campaign_of_current_user)
        time.sleep(SLEEP_TIME)
        assert_on_blasts_sends_url_conversion_and_activity(user_first.id, 1,
                                                           sms_campaign_of_current_user)
        delete_test_scheduled_task(task_id, valid_header)


class TestURLRedirectionApi(object):
    """
    This class contains tests for endpoint /v1/redirect/:id
    As response from Api endpoint is returned to candidate. So ,in case of any error,
    candidate should only get internal server error.
    """

    def test_for_get(self, user_first,
                     url_conversion_by_send_test_sms_campaign,
                     scheduled_sms_campaign_of_current_user):
        """
        GET method should give OK response. We check the "hit_count" and "clicks" before
        hitting the endpoint and after hitting the endpoint. Then we assert that both
        "hit_count" and "clicks" have been successfully updated by '1' in database.
        :return:
        """
        # stats before making HTTP GET request to source URL
        hit_count, clicks = _get_hit_count_and_clicks(url_conversion_by_send_test_sms_campaign,
                                                      scheduled_sms_campaign_of_current_user)
        response_get = _use_ngrok_or_local_address(
            'get', url_conversion_by_send_test_sms_campaign.source_url)
        assert response_get.status_code == 200, 'Response should be ok'
        # stats after making HTTP GET request to source URL
        hit_count_after, clicks_after = _get_hit_count_and_clicks(
            url_conversion_by_send_test_sms_campaign,
            scheduled_sms_campaign_of_current_user)
        assert hit_count_after == hit_count + 1
        assert clicks_after == clicks + 1
        assert_for_activity(user_first.id, Activity.MessageIds.CAMPAIGN_SMS_CLICK,
                            scheduled_sms_campaign_of_current_user.id)

    def test_get_with_no_signature(self, url_conversion_by_send_test_sms_campaign):
        """
        Removing signature of signed redirect URL. It should get internal server error.
        :return:
        """
        url_excluding_signature = \
            url_conversion_by_send_test_sms_campaign.source_url.split('?')[0]
        request_and_assert_internal_server_error(url_excluding_signature)

    def test_get_with_empty_destination_url(self, url_conversion_by_send_test_sms_campaign):
        """
        Making destination URL an empty string here, it should get internal server error.
        :return:
        """
        # forcing destination URL to be empty
        _make_destination_url_empty(url_conversion_by_send_test_sms_campaign)
        request_and_assert_internal_server_error(
            url_conversion_by_send_test_sms_campaign.source_url)

    def test_get_with_deleted_campaign(
            self, valid_header, scheduled_sms_campaign_of_current_user,
            url_conversion_by_send_test_sms_campaign):
        """
        Here we first delete the campaign, and then test functionality of url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should give ResourceNotFound Error.
        But candidate should get Internal server error. Hence this test should get internal server
        error.
        """
        _delete_sms_campaign(scheduled_sms_campaign_of_current_user, valid_header)
        request_and_assert_internal_server_error(
            url_conversion_by_send_test_sms_campaign.source_url)

    def test_get_with_deleted_candidate(self, url_conversion_by_send_test_sms_campaign,
                                        candidate_first, valid_header):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should get ResourceNotFound Error.
        But candidate should only get internal server error. So this test asserts we get internal
        server error.
        """
        _delete_candidate(candidate_first, valid_header)
        request_and_assert_internal_server_error(
            url_conversion_by_send_test_sms_campaign.source_url)

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
        :return:
        """
        _make_destination_url_empty(url_conversion_by_send_test_sms_campaign)
        try:
            _call_process_url_redirect(url_conversion_by_send_test_sms_campaign)
            assert None, 'EmptyDestinationUrl custom exception should be raised'
        except EmptyDestinationUrl as error:
            assert error.error_code == CampaignException.EMPTY_DESTINATION_URL

    def test_process_url_redirect_with_deleted_campaign(
            self, valid_header, sms_campaign_of_current_user,
            url_conversion_by_send_test_sms_campaign):
        """
        Here we first delete the campaign which internally deletes campaign send record,
        and then test functionality of url_redirect. It should give ResourceNotFound Error.
        """
        _delete_sms_campaign(sms_campaign_of_current_user, valid_header)
        _assert_for_no_campaign_send_obj(url_conversion_by_send_test_sms_campaign)

    def test_process_url_redirect_with_deleted_candidate(self, valid_header,
                                                         url_conversion_by_send_test_sms_campaign,
                                                         candidate_first):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of url_redirect().
        It should get ResourceNotFound Error.
        """
        _delete_candidate(candidate_first, valid_header)
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
            self, create_blast_for_not_owned_campaign,
            url_conversion_by_send_test_sms_campaign):
        """
        Here we pass None candidate, and then test functionality of
        validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
        It should give ResourceNotFound Error.
        """
        blast_obj = create_blast_for_not_owned_campaign
        _test_validate_blast_candidate_url_conversion_in_db(
            blast_obj, None, url_conversion_by_send_test_sms_campaign)

    def test_validate_blast_candidate_url_conversion_in_db_with_no_blast(
            self, candidate_first, url_conversion_by_send_test_sms_campaign):
        """
        Here we pass blast as None, and then test functionality of
        validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
        It should give ResourceNotFound Error.
        """
        _test_validate_blast_candidate_url_conversion_in_db(
            None, candidate_first, url_conversion_by_send_test_sms_campaign)

    def test_validate_blast_candidate_url_conversion_in_db_with_no_url_conversion(
            self, candidate_first, create_blast_for_not_owned_campaign):
        """
        Here we pass url_conversion obj  as None, and then test functionality of
        validate_blast_candidate_url_conversion_in_db() handy function in campaign_utils.py.
        It should give ResourceNotFound Error.
        """
        blast_obj = create_blast_for_not_owned_campaign
        _test_validate_blast_candidate_url_conversion_in_db(
            blast_obj, candidate_first, None)

    def test_pre_process_url_redirect_with_empty_data(self):
        """
        This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
        All parameters passed are None, So, it should raise Invalid Usage Error.
        :return:
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
        :param url_conversion_by_send_test_sms_campaign:
        :return:
        """
        request_args = _get_args_from_url(url_conversion_by_send_test_sms_campaign.source_url)
        _call_pre_process_url_redirect(request_args,
                                       url_conversion_by_send_test_sms_campaign.source_url)

    def test_pre_process_url_redirect_with_missing_key_signature(
            self, url_conversion_by_send_test_sms_campaign):
        """
        This tests the functionality of pre_process_url_redirect() class method of CampaignBase.
        signature is missing from request_arg.So, it should get Invalid Usage Error.
        :param url_conversion_by_send_test_sms_campaign:
        :return:
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
    response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % campaign.id,
                               headers=header)
    db.session.commit()
    assert response.status_code == 200, 'should get ok response (200)'


def request_and_assert_internal_server_error(url):
    """
    This makes HTTP GET call on given URL and assert that it receives internal server error.
    :param url:
    :return:
    """
    response_get = _use_ngrok_or_local_address('get', url)
    assert response_get.status_code == InternalServerError.http_status_code(), \
        'It should get Internal server error'


def _delete_candidate(candidate, headers):
    """
    This deletes the given candidate from candidate_service API.

    :return:
    """
    add_role_to_test_user(candidate.user, [DomainRole.Roles.CAN_DELETE_CANDIDATES])
    response = requests.delete(CandidateApiUrl.CANDIDATE % candidate.id, headers=headers)
    assert response.status_code == 204
    db.session.commit()


def _delete_url_conversion(url_conversion_obj):
    """
    This deletes the candidate of given id
    :param url_conversion_obj:
    :return:
    """
    UrlConversion.delete(url_conversion_obj)


def _test_validate_blast_candidate_url_conversion_in_db(blast, candidate, url_conversion_obj):
    """
    This tests the functionality of validate_blast_candidate_url_conversion_in_db() method in
        campaign_utils.py.
    :param blast:
    :param candidate:
    :param url_conversion_obj:
    :return:
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
    :return:
    """
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    sms_campaign_blasts = campaign.blasts[0]
    return url_conversion.hit_count, sms_campaign_blasts.clicks


def _get_args_from_url(url):
    """
    This gets the args from the signed URL
    :param url:
    :return:
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
    :param url_conversion_obj:
    :return:
    """
    with app.app_context():
        CampaignBase.url_redirect(url_conversion_obj.id, CampaignUtils.SMS)


def _call_pre_process_url_redirect(request_args, url):
    """
    This directly calls the pre_process_url_redirect() class method of CampaignBase
    :return:
    """
    with app.app_context():
        SmsCampaignBase.pre_process_url_redirect(request_args, url)


def _make_destination_url_empty(url_conversion_obj):
    """
    Here we make the destination URL an empty string.
    :param url_conversion_obj:
    :return:
    """
    url_conversion_obj.update(destination_url='')


def _assert_for_no_campaign_send_obj(url_conversion_obj):
    """
    This asserts the functionality of url_redirect() by deleting campaign from
    database.
    :param url_conversion_obj:
    :return:
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
