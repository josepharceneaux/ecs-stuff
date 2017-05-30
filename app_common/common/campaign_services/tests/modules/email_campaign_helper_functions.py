"""
This code contains helper common functions for email campaign service
"""
# Standard Imports
import json
from datetime import (datetime, timedelta)
# Third Party
import requests
from requests import codes
# Application Specific
from ....models.db import db
from ....models.misc import (Frequency, UrlConversion, Activity)
from ....utils.datetime_utils import DatetimeUtils
from ....utils.test_utils import (fake)
from ....routes import (EmailCampaignApiUrl)
from ...tests_helpers import CampaignsTestsHelpers
from ....models.email_campaign import EmailCampaign
from ....models.talent_pools_pipelines import TalentPipeline


def create_email_campaign_via_api(access_token, data, is_json=True):
    """
    This function makes HTTP POST call on /v1/email-campaigns to create
    an email-campaign. It then returns the response from email-campaigns API.
    :param access_token: access token of user
    :param data: data required for creation of campaign
    :param is_json: If True, it will take dumps of data to be sent in POST call. Otherwise it
                    will send data as it is.
    :return: response of API call
    """
    if is_json:
        data = json.dumps(data)
    response = requests.post(
        url=EmailCampaignApiUrl.CAMPAIGNS,
        data=data,
        headers={'Authorization': 'Bearer %s' % access_token,
                 'content-type': 'application/json'}
    )
    return response


def create_scheduled_email_campaign_data(access_token, talent_pipeline=None, **kwargs):
    """
    This returns data to create an scheduled email-campaign.
    :param access_token: User access token
    :param talent_pipeline: Talent pipeline object
    """
    if kwargs.get('talent_pipeline_id'):
        talent_pipeline_id = kwargs.get('talent_pipeline_id')
        db.session.commit()
        talent_pipeline = TalentPipeline.get(talent_pipeline_id)
    campaign_data = create_data_for_campaign_creation(access_token, talent_pipeline, **kwargs)
    campaign_data['frequency_id'] = Frequency.ONCE
    campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(weeks=1))
    campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow()
                                                             + timedelta(weeks=2))
    return campaign_data


def create_data_for_campaign_creation(access_token, talent_pipeline, subject=fake.name(),
                                      campaign_name=fake.name(), assert_candidates=True, create_smartlist=True,
                                      smartlist_id=None, **kwargs):
    """
    This function returns the required data to create an email campaign
    """
    body_text = fake.sentence()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    if create_smartlist:
        smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token,
                                                                                talent_pipeline,
                                                                                emails_list=True,
                                                                                assert_candidates=assert_candidates)
    return {'name': campaign_name,
            'subject': subject,
            'body_html': body_html,
            'frequency_id': Frequency.ONCE,
            'list_ids': [smartlist_id] if smartlist_id else []
            }


def assert_campaign_send(response, campaign, user_id, blast_sends=1, blasts_count=1, total_sends=None,
                         email_client=False, expected_status=codes.OK, abort_time_for_sends=300, via_amazon_ses=True,
                         delete_email=True):
    """
    This assert that campaign has successfully been sent to candidates and campaign blasts and
    sends have been updated as expected. It then checks the source URL is correctly formed or
    in database table "url_conversion".
    """
    if not total_sends:
        total_sends = blast_sends
    if type(campaign) == dict:
        db.session.commit()
        campaign = EmailCampaign.get_by_id(campaign['id'])

    msg_ids = ''
    assert response.status_code == expected_status
    assert response.json()
    if not email_client:
        json_resp = response.json()
        assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    CampaignsTestsHelpers.assert_campaign_blasts(campaign, expected_count=blasts_count, timeout=abort_time_for_sends)

    # assert on sends
    CampaignsTestsHelpers.assert_blast_sends(campaign, blast_index=blasts_count - 1, expected_count=blast_sends,
                                             abort_time_for_sends=abort_time_for_sends)
    campaign_sends = campaign.sends.all()
    assert len(campaign_sends) == total_sends
    sends_url_conversions = []
    # assert on activity of individual campaign sends
    for campaign_send in campaign_sends:
        # Get "email_campaign_send_url_conversion" records
        sends_url_conversions.extend(campaign_send.url_conversions)
        if not email_client:
            if via_amazon_ses:  # If email-campaign is sent via Amazon SES, we should have message_id and request_id
                # saved in database table "email_campaign_sends"
                assert campaign_send.ses_message_id
                assert campaign_send.ses_request_id  # TODO: Won't be needed in boto3
            if campaign.base_campaign_id:
                CampaignsTestsHelpers.assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_EVENT_SEND,
                                                          campaign_send.id)
            else:
                CampaignsTestsHelpers.assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_EMAIL_SEND,
                                                          campaign_send.id)
    if campaign_sends:
        # assert on activity for whole campaign send
        # TODO: commenting this for now, will debug in GET-2471
        CampaignsTestsHelpers.assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_SEND, campaign.id)
        # TODO: Emails are being delayed, commenting for now
        # if not email_client:
        #     msg_ids = retry(assert_and_delete_email, sleeptime=5, attempts=80, sleepscale=1,
        #                     args=(campaign.subject,), kwargs=dict(delete_email=delete_email),
        #                     retry_exceptions=(AssertionError, imaplib.IMAP4_SSL.error))
        #
        #     assert msg_ids, "Email with subject %s was not found at time: %s." % (campaign.subject,
        #                                                               str(datetime.utcnow()))
    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        assert str(send_url_conversion.url_conversion.id) in send_url_conversion.url_conversion.source_url
        UrlConversion.delete(send_url_conversion.url_conversion)
    return msg_ids
