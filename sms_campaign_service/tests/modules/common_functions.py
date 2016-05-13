"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains the code which is common for different tests.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.models.db import db
from sms_campaign_service.sms_campaign_app import app
from sms_campaign_service.common.tests.conftest import fake
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.misc import (UrlConversion, Activity)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaignReply,
                                                             SmsCampaign)
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from sms_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    get_candidates_of_smartlist


def assert_url_conversion(sms_campaign_sends):
    """
    This function verifies that source_url saved in database table "url_conversion" is in
    valid format as expected.

    URL to redirect candidate to our app looks like e.g.

    http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0&auth_user=no_user&extra=
                &signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D)

    So we will verify whether source_url has url_conversion id in it.
    """
    sends_url_conversions = []
    # Get "sms_campaign_send_url_conversion" records
    for sms_campaign_send in sms_campaign_sends:
        sends_url_conversions.extend(sms_campaign_send.url_conversions)
    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        url_conversion_id = str(send_url_conversion.url_conversion.id)
        source_url = send_url_conversion.url_conversion.source_url
        assert url_conversion_id in source_url
        UrlConversion.delete(send_url_conversion.url_conversion)


def assert_on_blasts_sends_url_conversion_and_activity(user_id, expected_sends, campaign_id,
                                                       access_token,
                                                       expected_blasts=1,
                                                       blast_index=0, blast_timeout=10,
                                                       sends_timeout=30):
    """
    This function assert the number of sends in database table "sms_campaign_blast" and
    records in database table "sms_campaign_sends"
    """
    # TODO: This will be removed when working on removing DB connections
    campaign = SmsCampaign.get_by_id(campaign_id)
    # assert on blasts
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    # GET blasts of given campaign
    CampaignsTestsHelpers.assert_campaign_blasts(campaign, expected_blasts,
                                                 access_token=access_token,
                                                 blasts_url=SmsCampaignApiUrl.BLASTS % campaign.id,
                                                 timeout=blast_timeout)
    # Get sms-campaign-blast object
    sms_campaign_blast = CampaignsTestsHelpers.get_blast_by_index_with_polling(campaign,
                                                                               blast_index)
    # Poll blast sends
    CampaignsTestsHelpers.assert_blast_sends(campaign, expected_sends, blast_index=blast_index,
                                             abort_time_for_sends=sends_timeout)

    assert sms_campaign_blast.sends == expected_sends
    # assert on sends
    sms_campaign_sends = sms_campaign_blast.blast_sends.all()
    assert len(sms_campaign_sends) == expected_sends
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
    """
    CampaignsTestsHelpers.assert_for_activity(user_id, type_, source_id)


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
    campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
    assert str(campaign_id) in json_resp['message']


def assert_campaign_schedule(response, user_id, campaign_id):
    """
    This asserts that campaign has scheduled successfully and we get 'task_id' in response
    """
    assert response.status_code == 200, response.json()['error']['message']
    assert 'task_id' in response.json()
    assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_SCHEDULE, campaign_id)
    return response.json()['task_id']


def assert_campaign_delete(response, user_id, campaign_id):
    """
    This asserts the response of campaign deletion and asserts that activity has been
    created successfully.
    """
    assert response.status_code == 200, 'should get ok response(200)'
    assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_DELETE, campaign_id)


def delete_test_scheduled_task(task_id, headers):
    """
    This deletes the scheduled task from scheduler_service
    """
    with app.app_context():
        CampaignUtils.delete_scheduled_task(task_id, headers)


def assert_campaign_creation(response, user_id, expected_status_code):
    """
    Here are asserts that make sure that campaign has been created successfully.
    It returns id of created SMS campaign.
    """
    assert response.status_code == expected_status_code, \
        'It should get status code ' + str(expected_status_code)
    assert response.json()
    json_response = response.json()
    assert 'location' in response.headers
    assert 'id' in json_response
    assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_CREATE, json_response['id'])
    return json_response['id']


def candidate_ids_associated_with_campaign(campaign, access_token, smartlist_index=0):
    """
    This returns candidate_ids associated with the smartlists of given campaign object.
    :param campaign: SMS campaign object
    :param access_token: access token of user
    """
    return get_candidates_of_smartlist(campaign['list_ids'][smartlist_index], True, access_token)


def reply_and_assert_response(campaign_obj, user_phone, candidate_phone, access_token,
                              reply_count=1):
    """
    We reply to a campaign by hitting /v1/receive endpoint.
    We then assert that all the expected entries have been created in database.
    """
    reply_text = fake.sentence()
    reply_count_before = get_replies_count(campaign_obj, access_token)
    response_get = requests.post(SmsCampaignApiUrl.RECEIVE,
                                 data={'To': user_phone.value,
                                       'From': candidate_phone['value'],
                                       'Body': reply_text})
    assert response_get.status_code == requests.codes.OK, 'Response should be ok'
    assert 'xml' in str(response_get.text).strip()
    campaign_reply_in_db = get_campaign_reply(candidate_phone)
    assert len(campaign_reply_in_db) == reply_count
    assert campaign_reply_in_db[reply_count - 1].body_text == reply_text
    reply_count_after = get_replies_count(campaign_obj, access_token)
    assert reply_count_after == reply_count_before + 1
    assert_for_activity(user_phone.user_id, Activity.MessageIds.CAMPAIGN_SMS_REPLY,
                        campaign_reply_in_db[reply_count - 1].id)


def get_campaign_reply(candidate_phone):
    """
    This asserts that exact reply of candidate has been saved in database table "sms_campaign_reply"
    """
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    candidate_phone_id = candidate_phone.id if hasattr(candidate_phone, 'id') else candidate_phone[
        'id']
    campaign_reply_record = SmsCampaignReply.get_by_candidate_phone_id(candidate_phone_id)
    return campaign_reply_record


def get_replies_count(campaign, access_token):
    """
    This returns the replies counts of SMS campaign from database table 'sms_campaign_blast'
    :param campaign: SMS campaign obj
    :param access_token: Access token of user
    """
    sms_campaign_blasts = CampaignsTestsHelpers.get_blasts_with_polling(campaign,
                                                                        access_token,
                                                                        blasts_url=SmsCampaignApiUrl.BLASTS %
                                                                                   campaign['id'])
    return sms_campaign_blasts[0]['replies']


def assert_valid_reply_object(received_reply_obj, expected_blast_id, candidate_phone_ids):
    """
    Here we are asserting that response from API
    1- /v1/sms-campaigns/:campaign_id/replies
    2- /v1/sms-campaigns/:campaign_id/blasts/:blast_id/replies has all required fields in it.
    :param (dict) received_reply_obj: object received from above API endpoints
    :param (int, long) expected_blast_id: Id of campaign blast
    :param (list[int | long]) candidate_phone_ids: list of candidate phone ids
    """
    assert received_reply_obj['id']
    assert received_reply_obj['body_text']
    assert received_reply_obj['added_datetime']
    assert received_reply_obj['blast_id'] == expected_blast_id
    assert received_reply_obj['candidate_phone_id'] in candidate_phone_ids


def assert_valid_campaign_get(campaign_dict, referenced_campaign, compare_fields=True):
    """
    This asserts that the sms-campaign we get from GET http request has same fields as we expect
    :param (dict) campaign_dict: sms-campaign dict received from HTTP GET
    :param (dict) referenced_campaign: sms-campaign object with which we are comparing
    :param (bool) compare_fields: If True, it will compare values of respective fields of both
                campaigns, otherwise it will only asserts that expected fields are present.
    """
    # TODO: Update this for user-defined fields in GET-1260
    if compare_fields:
        for field in campaign_dict.keys():
            assert campaign_dict[field] == referenced_campaign[field]
    else:
        assert campaign_dict['id']
        assert campaign_dict['name']
        assert campaign_dict['body_text']
        assert campaign_dict['list_ids']
        assert campaign_dict['user_id']
        CampaignsTestsHelpers.assert_valid_datetime_range(campaign_dict['added_datetime'])


def assert_valid_blast_object(received_blast_obj, expected_blast_id, campaign_id, expected_sends=0,
                              expected_replies=0, expected_clicks=0):
    """
    Here we are asserting that response from API
    1- /v1/sms-campaigns/:campaign_id/blasts
    2- /v1/sms-campaigns/:campaign_id/blasts/:blast_id has all required fields in it.
    :param (dict) received_blast_obj: object received from above API endpoints
    :param (int | long) expected_blast_id: Id of campaign blast
    :param (int | long) campaign_id: Id of sms-campaign
    :param (int | long) expected_sends: Number of sends for given campaign
    :param (int | long) expected_replies: Number of replies for given campaign
    :param (int | long) expected_clicks: Number of clicks for given campaign
    """
    assert received_blast_obj['id'] == expected_blast_id
    assert received_blast_obj['campaign_id'] == campaign_id
    assert received_blast_obj['sends'] == expected_sends
    assert received_blast_obj['replies'] == expected_replies
    assert received_blast_obj['clicks'] == expected_clicks
    CampaignsTestsHelpers.assert_valid_datetime_range(received_blast_obj['sent_datetime'])
    CampaignsTestsHelpers.assert_valid_datetime_range(received_blast_obj['updated_time'])


def assert_valid_send_object(received_send_obj, expected_blast_id, candidate_ids):
    """
    Here we are asserting that response from API
    1- /v1/sms-campaigns/:campaign_id/sends
    2- /v1/sms-campaigns/:campaign_id/blasts/:blast_id/sends has all required fields in it.
    :param (dict) received_send_obj: object received from above API endpoints
    :param (int, long) expected_blast_id: Id of campaign blast
    :param (list[int | long]) candidate_ids: list of candidate ids
    """
    assert received_send_obj['id']
    assert received_send_obj['blast_id'] == expected_blast_id
    assert received_send_obj['candidate_id'] in candidate_ids
    CampaignsTestsHelpers.assert_valid_datetime_range(received_send_obj['sent_datetime'])
    CampaignsTestsHelpers.assert_valid_datetime_range(received_send_obj['updated_time'])
