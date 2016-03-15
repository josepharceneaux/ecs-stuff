"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains the code which is common for different tests.
"""
# Standard Import
import time

# Common Utils
from sms_campaign_service.sms_campaign_app import app
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.models.misc import (UrlConversion, Activity)
from sms_campaign_service.common.models.sms_campaign import SmsCampaignReply
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

SLEEP_TIME = 30


def assert_url_conversion(sms_campaign_sends):
    """
    This function verifies that source_url saved in database table "url_conversion" is in
    valid format as expected.

    URL to redirect candidate to our app looks like e.g.

    http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0&auth_user=no_user&extra=
                &signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D)

    So we will verify whether source_url has url_conversion id in it.

    :param sms_campaign_sends: sends of campaign
    :return:
    """
    sends_url_conversions = []
    # Get "sms_campaign_send_url_conversion" records
    for sms_campaign_send in sms_campaign_sends:
        sends_url_conversions.extend(sms_campaign_send.url_conversions)
    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        assert str(send_url_conversion.url_conversion.id) in send_url_conversion.url_conversion.source_url
        UrlConversion.delete(send_url_conversion.url_conversion)


def assert_on_blasts_sends_url_conversion_and_activity(user_id, expected_count, campaign):
    """
    This function assert the number of sends in database table "sms_campaign_blast" and
    records in database table "sms_campaign_sends"
    :param expected_count: Expected number of sends
    :return:
    """
    # assert on blasts
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    sms_campaign_blast = campaign.blasts[0]
    assert sms_campaign_blast.sends == expected_count
    # assert on sends
    sms_campaign_sends = sms_campaign_blast.blast_sends
    assert len(sms_campaign_sends) == expected_count
    # assert on activity of individual campaign sends
    for sms_campaign_send in sms_campaign_sends:
        assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_SMS_SEND, sms_campaign_send.id)
    if sms_campaign_sends:
        # assert on activity for whole campaign send
        assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_SEND, campaign.id)
    assert_url_conversion(sms_campaign_sends)


def assert_for_activity(user_id, type_, source_id):
    """
    This verifies that activity has been created for given action
    :param user_id:
    :param type_:
    :param source_id:
    :return:
    """
    CampaignsTestsHelpers.assert_for_activity(user_id, type_, source_id)


def get_reply_text(candidate_phone):
    """
    This asserts that exact reply of candidate has been saved in database table "sms_campaign_reply"
    :param candidate_phone:
    :return:
    """
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    time.sleep(2*SLEEP_TIME)
    db.session.commit()
    campaign_reply_record = SmsCampaignReply.get_by_candidate_phone_id(candidate_phone.id)
    return campaign_reply_record


def assert_api_send_response(campaign, response, expected_status_code):
    """
    Here are asserts that make sure that campaign has been created successfully.
    :param campaign: sms_campaign obj
    :param response: HTTP POST response
    :param expected_status_code: status code like 200, 404
    """
    assert response.status_code == expected_status_code, \
        'Response should be ' + str(expected_status_code)
    assert response.json()
    json_resp = response.json()
    assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    time.sleep(2*SLEEP_TIME)


def assert_campaign_schedule(response, user_id, campaign_id):
    """
    This asserts that campaign has scheduled successfully and we get 'task_id' in response
    :param response:
    :return:
    """
    assert response.status_code == 200, response.json()['error']['message']
    assert 'task_id' in response.json()
    assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_SCHEDULE, campaign_id)
    return response.json()['task_id']


def assert_campaign_delete(response, user_id, campaign_id):
    """
    This asserts the response of campaign deletion and asserts that activity has been
    created successfully.
    :return:
    """
    assert response.status_code == 200, 'should get ok response(200)'
    assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_DELETE, campaign_id)


def delete_test_scheduled_task(task_id, headers):
    """
    This deletes the scheduled task from scheduler_service
    :param task_id:
    :param headers:
    :return:
    """
    with app.app_context():
        CampaignUtils.delete_scheduled_task(task_id, headers)
