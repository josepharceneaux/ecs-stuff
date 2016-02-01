import os
import re
import json
import datetime
import requests

from sqlalchemy import and_
from sqlalchemy import desc
from email_campaign_service.modules.utils import (create_email_campaign_url_conversions, do_mergetag_replacements,
                                                  get_candidates_of_smartlist, TRACKING_URL_TYPE)
from email_campaign_service.email_campaign_app import logger
from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.email_marketing import (EmailCampaign, EmailCampaignSmartList,
                                                                  EmailCampaignBlast, EmailCampaignSend,
                                                                  EmailCampaignSendUrlConversion)
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.models.user import User, Domain
from email_campaign_service.common.models.candidate import Candidate, CandidateEmail, CandidateSubscriptionPreference
from email_campaign_service.common.error_handling import *
from email_campaign_service.common.utils.talent_reporting import email_notification_to_admins
from email_campaign_service.common.utils.amazon_ses import send_email
from email_campaign_service.common.inter_service_calls.activity_service_calls import add_activity, ActivityTypes
from email_campaign_service.common.routes import SchedulerApiUrl, EmailCampaignUrl
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.utils.scheduler_utils import SchedulerUtils
from email_campaign_service.common.utils.candidate_service_calls import get_candidate_subscription_preference

__author__ = 'jitesh'


def create_email_campaign_smartlists(smartlist_ids, email_campaign_id):
    """ Maps smart lists to email campaign
    :param smartlist_ids:
    :type smartlist_ids: list[int | long]
    :param email_campaign_id: id of email campaign to which smart lists will be associated.

    """
    if type(smartlist_ids) in (int, long):
        smartlist_ids = [smartlist_ids]
    for smartlist_id in smartlist_ids:
        email_campaign_smartlist = EmailCampaignSmartList(smartlist_id=smartlist_id,
                                                           email_campaign_id=email_campaign_id)
        db.session.add(email_campaign_smartlist)
    db.session.commit()


def create_email_campaign(user_id, oauth_token, email_campaign_name, email_subject,
                          email_from, email_reply_to, email_body_html,
                          email_body_text, list_ids, email_client_id=None,
                          frequency=None,
                          send_time=None,
                          stop_time=None,
                          template_id=None):
    """
    Creates a new email campaign.
    Schedules email campaign.

    :return: newly created email_campaign's id
    """
    frequency_obj = Frequency.get_frequency_from_name(frequency) if frequency else None

    email_campaign = EmailCampaign(name=email_campaign_name,
                                   user_id=user_id,
                                   is_hidden=0,
                                   email_subject=email_subject,
                                   email_from=email_from,
                                   email_reply_to=email_reply_to,
                                   email_body_html=email_body_html,
                                   email_body_text=email_body_text,
                                   send_time=send_time,
                                   stop_time=stop_time,
                                   frequency_id=frequency_obj.id if frequency_obj else None,
                                   email_client_id=email_client_id
                                   )

    db.session.add(email_campaign)
    db.session.commit()

    # Add activity
    add_activity(user_id=user_id,
                 oauth_token=oauth_token,
                 activity_type=ActivityTypes.CAMPAIGN_CREATE,
                 source_id=email_campaign.id, source_table=EmailCampaign.__tablename__,
                 params=dict(id=email_campaign.id, name=email_campaign_name))

    # create email_campaign_smartlist record
    create_email_campaign_smartlists(smartlist_ids=list_ids,
                                      email_campaign_id=email_campaign.id)

    # if it's a client from api, we don't schedule campaign sends, we create it on the fly.
    # also we enable tracking by default for the clients.
    if email_client_id:
        # If email is sent via email_client then enable tracking.
        email_campaign.isEmailOpenTracking = 1
        email_campaign.isTrackHtmlClicks = 1
        email_campaign.isTrackTextClicks = 1
        db.session.commit()  # Commit the changes
        # Actual emails are sent from the client. So no need to schedule it
        # TODO: Update campaign status to 'completed'
        return {'id': email_campaign.id}

    # Schedule the sending of emails & update email_campaign scheduler fields
    schedule_task_params = {
        "url": EmailCampaignUrl.SEND_CAMPAIGN % email_campaign.id,
        "content_type": "application/json",
    }
    if frequency_obj and frequency_obj.name != 'once':
        schedule_task_params["frequency"] = frequency_obj.in_seconds()
        schedule_task_params["task_type"] = SchedulerUtils.PERIODIC  # Change task_type to periodic
        schedule_task_params["start_datetime"] = send_time
        schedule_task_params["end_datetime"] = stop_time
    elif frequency_obj and frequency_obj.name == 'once':
        schedule_task_params["task_type"] = SchedulerUtils.ONE_TIME
        schedule_task_params["start_datetime"] = send_time
        schedule_task_params["end_datetime"] = send_time
    else:
        schedule_task_params["task_type"] = SchedulerUtils.ONE_TIME
        schedule_task_params["run_datetime"] = (datetime.datetime.utcnow() + datetime.timedelta(seconds=10)).strftime(
            "%Y-%m-%d %H:%M:%S")

    # Schedule email campaign; call Scheduler API
    headers = {'Authorization': oauth_token, 'Content-Type': 'application/json'}
    try:
        scheduler_response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(schedule_task_params))
    except Exception as ex:
        logger.exception('Exception occurred while calling scheduler. Exception: %s' % ex)
        raise
    if scheduler_response.status_code != 201:
        raise InternalServerError("Error occurred while scheduling email campaign. Status Code: %s, Response: %s" % (scheduler_response.status_code, scheduler_response.json()))
    scheduler_id = scheduler_response.json()['id']
    # add scheduler task id to email_campaign.
    email_campaign.scheduler_task_id = scheduler_id
    db.session.commit()

    return {'id': email_campaign.id}


def send_emails_to_campaign(oauth_token, campaign, list_ids=None, new_candidates_only=False, email_client_id=None):
    """
    new_candidates_only sends the emails only to candidates who haven't yet
    received any as part of this campaign.

    :param campaign:    email campaign object
    :param list_ids: list associated with email campaign if given it will take the ids provided else extract out from email campaign object
    :param new_candidates_only: If emails need to be sent to new candidates only i.e. to those candidates whom emails were not sent previously
    :param email_client_id: email_client id if email is sent from email_client.
        If email is sent from client it will not send the actual emails and returns the new html (with url conversions and other replacements)
    :return:            number of emails sent
    """
    user = campaign.user
    emails_sent = 0
    candidate_ids_and_emails = get_email_campaign_candidate_ids_and_emails(oauth_token, campaign=campaign,
                                                                           list_ids=list_ids,
                                                                           new_candidates_only=new_candidates_only)

    # Check if the smart list has more than 0 candidates
    if len(candidate_ids_and_emails) > 0:
        email_notification_to_admins(
                subject='Marketing batch about to send',
                body="Marketing email batch about to send, campaign.name=%s, user=%s, \
        new_candidates_only=%s, address list size=%s" % (
                    campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)
                )
        )
        logger.info("Marketing email batch about to send, campaign.name=%s, user=%s, "
                                "new_candidates_only=%s, address list size=%s" % (
                                    campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)))

        # Add activity
        add_activity(user_id=user.id,
                     oauth_token=oauth_token,
                     activity_type=ActivityTypes.CAMPAIGN_SEND,
                     source_id=campaign.id, source_table=EmailCampaign.__tablename__,
                     params=dict(id=campaign.id, name=campaign.name, num_candidates=len(candidate_ids_and_emails)))

        # Create the email_campaign_blast for this blast
        blast_datetime = datetime.datetime.now()
        email_campaign_blast = EmailCampaignBlast(email_campaign_id=campaign.id, sent_time=blast_datetime)
        db.session.add(email_campaign_blast)
        db.session.commit()
        blast_params = dict(sends=0, bounces=0)

        # For each candidate, create URL conversions and send the email
        list_of_new_email_html_or_text = []
        for candidate_id, candidate_address in candidate_ids_and_emails:

            was_send = send_campaign_emails_to_candidate(
                user=user,
                oauth_token=oauth_token,
                campaign=campaign,
                candidate=Candidate.query.get(candidate_id),
                # candidates.find(lambda row: row.id == candidate_id).first(),
                candidate_address=candidate_address,
                blast_params=blast_params,
                email_campaign_blast_id=email_campaign_blast.id,
                blast_datetime=blast_datetime,
                email_client_id=campaign.email_client_id
            )

            if campaign.email_client_id:
                resp_dict = {}
                resp_dict['new_html'] = was_send.get('new_html')
                resp_dict['new_text'] = was_send.get('new_text')
                resp_dict['email'] = candidate_address
                list_of_new_email_html_or_text.append(resp_dict)

            if was_send:
                emails_sent += 1

            db.session.commit()
    logger.info("Marketing email batch completed, emails sent=%s, campaign=%s, user=%s, new_candidates_only=%s",
            emails_sent, campaign.name, user.email, new_candidates_only)

    if campaign.email_client_id:
        return list_of_new_email_html_or_text

    return emails_sent


def get_email_campaign_candidate_ids_and_emails(oauth_token, campaign, list_ids=None,
                                                new_candidates_only=False):
    """
    :param campaign:    email campaign row
    :param user:        user row
    :return:            Returns array of candidate IDs in the campaign's smartlists.
                        Is unique.
    """
    if list_ids is None:
        # Get smartlists of this campaign
        list_ids = EmailCampaignSmartList.get_smartlists_of_campaign(campaign.id, smartlist_ids_only=True)
    # Get candidate ids
    all_candidate_ids = []
    for list_id in list_ids:
        # Get candidates present in smartlist
        smartlist_candidate_ids = get_candidates_of_smartlist(oauth_token, list_id, candidate_ids_only=True)
        # gather all candidates from various smartlists
        all_candidate_ids.extend(smartlist_candidate_ids)

    all_candidate_ids = list(set(all_candidate_ids))  # Unique candidates

    if campaign.is_subscription:
        # If the campaign is a subscription campaign,
        # only get candidates subscribed to the campaign's frequency
        subscribed_candidates_rows = CandidateSubscriptionPreference.with_entities(
            CandidateSubscriptionPreference.candidate_id).filter(
            and_(CandidateSubscriptionPreference.candidate_id.in_(all_candidate_ids),
                 CandidateSubscriptionPreference.frequency_id == campaign.frequency_id)).all()
        subscribed_candidate_ids = [row.candidate_id for row in subscribed_candidates_rows]  # Subscribed candidate ids
        if not subscribed_candidate_ids:
            logger.error("No candidates in subscription campaign %s", campaign)

    else:
        # Otherwise, just filter out unsubscribed candidates:
        # their subscription preference's frequencyId is NULL, which means 'Never'
        unsubscribed_candidate_ids = []
        for candidate_id in all_candidate_ids:
            # Call candidate API to get candidate's subscription preference.
            subscription_preference = get_candidate_subscription_preference(oauth_token, candidate_id)
            # campaign_subscription_preference = get_subscription_preference(candidate_id)
            logger.debug("subscription_preference: %s" % subscription_preference)
            if subscription_preference and not subscription_preference.get('frequency_id'):
                unsubscribed_candidate_ids.append(candidate_id)
        # Remove unsubscribed candidates
        subscribed_candidate_ids = list(set(all_candidate_ids) - set(unsubscribed_candidate_ids))

    # If only getting candidates that haven't been emailed before...
    if new_candidates_only:
        already_emailed_candidates = EmailCampaignSend.query.with_entities(
            EmailCampaignSend.candidate_id).filter_by(email_campaign_id=campaign.id).all()
        emailed_candidate_ids = [row.candidate_id for row in already_emailed_candidates]

        # Filter out already emailed candidates from subscribed_candidate_ids, so we have new candidate_ids only
        new_candidate_ids = list(set(subscribed_candidate_ids) - set(emailed_candidate_ids))
        # assign it to subscribed_candidate_ids (doing it explicit just to make it clear)
        subscribed_candidate_ids = new_candidate_ids

    # Get emails
    candidate_email_rows = CandidateEmail.query.with_entities(CandidateEmail.candidate_id, CandidateEmail.address) \
        .filter(CandidateEmail.candidate_id.in_(subscribed_candidate_ids)) \
        .group_by(CandidateEmail.address)
    # list of tuples (candidate id, email address)
    return [(row.candidate_id, row.address) for row in candidate_email_rows]


def send_campaign_emails_to_candidate(user, oauth_token, campaign, candidate, candidate_address,
                                      blast_params=None, email_campaign_blast_id=None,
                                      blast_datetime=None, do_email_business=None,
                                      email_client_id=None):
    """
    :param user: user row
    :param campaign: email campaign row
    :param candidate: candidate row
    """
    # Set the email campaign blast fields if they're not defined, like if this just a test
    if not email_campaign_blast_id:
        email_campaign_blast = EmailCampaignBlast.query.filter(
            EmailCampaignBlast.email_campaign_id == campaign.id).order_by(desc(EmailCampaignBlast.sent_time)).first()
        if not email_campaign_blast:
            logger.error("""send_campaign_emails_to_candidate: Must have a previous email_campaign_blast
             that belongs to this campaign if you don't pass in the email_campaign_blast_id param""")
            return False
        email_campaign_blast_id = email_campaign_blast.id
        blast_datetime = email_campaign_blast.sentTime
    if not blast_datetime:
        blast_datetime = datetime.datetime.now()
    if not blast_params:
        email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
        blast_params = dict(sends=email_campaign_blast.sends, bounces=email_campaign_blast.bounces)
    email_campaign_send = EmailCampaignSend(email_campaign_id=campaign.id, candidate_id=candidate.id,
                                            sent_time=blast_datetime)
    db.session.add(email_campaign_send)
    db.session.commit()
    # If the campaign is a subscription campaign, its body & subject are candidate-specific and will be set here
    if campaign.is_subscription:
        pass
    #             from TalentJobAlerts import get_email_campaign_fields TODO: Job Alerts?
    #             campaign_fields = get_email_campaign_fields(candidate.id, do_email_business=do_email_business)
    #             if campaign_fields['total_openings'] < 1:  # If candidate has no matching job openings, don't send the email
    #                 return 0
    #             for campaign_field_name, campaign_field_value in campaign_fields.items():
    #                 campaign[campaign_field_name] = campaign_field_value
    new_html, new_text = campaign.email_body_html or "", campaign.email_body_text or ""

    # Perform MERGETAG replacements
    [new_html, new_text, subject] = do_mergetag_replacements([new_html, new_text, campaign.email_subject], candidate)
    # Perform URL conversions and add in the custom HTML
    new_text, new_html = create_email_campaign_url_conversions(new_html=new_html,
                                                               new_text=new_text,
                                                               is_track_text_clicks=campaign.is_track_text_clicks,
                                                               is_track_html_clicks=campaign.is_track_html_clicks,
                                                               custom_url_params_json=campaign.custom_url_params_json,
                                                               is_email_open_tracking=campaign.is_email_open_tracking,
                                                               custom_html=campaign.custom_html,
                                                               email_campaign_send_id=email_campaign_send.id)
    # Only in case of production we should send mails to candidate address else mails will go to test account.
    # To avoid spamming actual email addresses, while testing.
    if os.getenv(TalentConfigKeys.ENV_KEY) is 'prod':
        to_addresses = candidate_address
    else:
        # In dev/staging, only send emails to getTalent users, in case we're impersonating a customer.
        domain = Domain.query.get(user.domain_id)
        domain_name = domain.name.lower()
        if 'gettalent' in domain_name or 'bluth' in domain_name or 'dice' in domain_name:
            to_addresses = user.email
        else:
            to_addresses = ['gettalentmailtest@gmail.com']
    # Do not send mail if email_client_id is provided
    if email_client_id:
        logger.info("Marketing email added through client %s", email_client_id)
        return dict(new_html=new_html, new_text=new_text)
    else:
        try:
            email_response = send_email(source='"%s" <no-reply@gettalent.com>' % campaign.email_from,
                                        # Emails will be sent from <no-reply@gettalent.com> (verified by Amazon SES)
                                        subject=subject,
                                        html_body=new_html or None,
                                        # Can't be '', otherwise, text_body will not show in email
                                        text_body=new_text,
                                        to_addresses=to_addresses,
                                        reply_address=campaign.email_reply_to,
                                        # BOTO doesn't seem to work with an array as to_addresses
                                        body=None,
                                        email_format='html' if campaign.email_body_html else 'text')
        except Exception as e:
            # Mark email as bounced
            _mark_email_bounced(email_campaign_send, candidate, to_addresses, blast_params, email_campaign_blast_id, e)
            return False
        # Save SES message ID & request ID
        logger.info("Marketing email sent to %s. Email response=%s", to_addresses, email_response)
        request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
        message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
        email_campaign_send.ses_message_id = message_id
        email_campaign_send.ses_request_id = request_id
        db.session.commit()
        # Add activity
        add_activity(user_id=user.id, oauth_token=oauth_token, activity_type=ActivityTypes.CAMPAIGN_EMAIL_SEND,
                     source_id=email_campaign_send.id, source_table=EmailCampaignSend.__tablename__,
                     params=dict(candidateId=candidate.id, campaign_name=campaign.name,
                                 candidate_name=candidate.formatted_name))

    # Update blast
    blast_params['sends'] += 1
    email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
    email_campaign_blast.sends = blast_params['sends']
    db.session.commit()

    return True


def _mark_email_bounced(email_campaign_send, candidate, to_addresses, blast_params, email_campaign_blast_id, exception):
    """ If failed to send email; Mark email bounced.
    """
    # If failed to send email, still try to get request id from XML response.
    # Unfortunately XML response is malformed so must manually parse out request id
    request_id_search = re.search('<RequestId>(.*)</RequestId>', exception.__str__(), re.IGNORECASE)
    request_id = request_id_search.group(1) if request_id_search else None
    # email_campaign_send = EmailCampaignSend.query.get(email_campaign_send_id)
    email_campaign_send.is_ses_bounce = 1
    email_campaign_send.ses_request_id = request_id
    db.session.commit()
    # Update blast
    blast_params['bounces'] += 1
    email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
    email_campaign_blast.bounces = blast_params['bounces']
    db.session.commit()
    # Send failure message to email marketing admin, just to notify for verification
    logger.exception(
            "Failed to send marketing email to candidate_id=%s, to_addresses=%s" % (candidate.id, to_addresses))


def update_hit_count(url_conversion):
    try:
        # Increment hit count for email marketing
        new_hit_count = (url_conversion.hit_count or 0) + 1
        url_conversion.hit_count=new_hit_count
        url_conversion.last_hit_time=datetime.datetime.now()
        db.session.commit()
        email_campaign_send_url_conversion = EmailCampaignSendUrlConversion.query.filter_by(url_conversion_id=url_conversion.id).first()
        email_campaign_send = email_campaign_send_url_conversion.email_campaign_send
        candidate = Candidate.query.get(email_campaign_send.candidate_id)
        is_open = email_campaign_send_url_conversion.type == TRACKING_URL_TYPE
        if candidate:  # If candidate has been deleted, don't make the activity
            # Add activity
            add_activity(user_id="?", oauth_token="?",
                         activity_type=ActivityTypes.CAMPAIGN_EMAIL_OPEN if is_open else ActivityTypes.CAMPAIGN_EMAIL_CLICK,
                         source_id=email_campaign_send.id, source_table=EmailCampaignSend.__tablename__,
                         params=dict(candidateId=candidate.id, campaign_name=email_campaign_send.email_campaign.name,
                                     candidate_name=candidate.formatted_name))
        else:
            logger.info("Tried performing URL redirect for nonexistent candidate: %s. email_campaign_send: %s",
                        email_campaign_send.candidate_id, email_campaign_send.id)

        # Update email_campaign_blast entry only if it's a new hit
        if new_hit_count == 1:
            email_campaign_blast = EmailCampaignBlast.query.filter_by(and_(send_time=email_campaign_send.send_time,
                                                                           email_campaign_id=email_campaign_send.email_campaign_id)).first()
            if email_campaign_blast:
                if is_open:
                    email_campaign_blast.opens += 1
                else:
                    email_campaign_blast.html_clicks += 1
                db.session.commit()
            else:
                logger.error("Email campaign URL redirect: No email_campaign_blast found matching "
                             "email_campaign_send.sentTime %s, campaign_id=%s" % (email_campaign_send.sent_time,
                                                                                  email_campaign_send.email_campaign_id)
                             )
    except Exception:
        logger.exception("Received exception doing url_redirect (url_conversion_id=%s)", url_conversion.id)


def get_subscription_preference(candidate_id):
    """
    If there are multiple subscription preferences (due to legacy reasons),
    if any one is 1-6, keep it and delete the rest.
    Otherwise, if any one is NULL, keep it and delete the rest.
    Otherwise, if any one is 7, delete all of them.
    """
    # Not used but keeping it because same function was somewhere else in other service but using hardcoded ids.
    # So this one can be used to replace the old function.
    email_prefs = db.session.query(CandidateSubscriptionPreference).filter_by(candidate_id=candidate_id)
    non_custom_frequencies = db.session.query(Frequency.id).filter(
        Frequency.name.in_(Frequency.standard_frequencies().keys())).all()
    non_custom_frequency_ids = [non_custom_frequency[0] for non_custom_frequency in non_custom_frequencies]
    non_custom_pref = email_prefs.filter(
        CandidateSubscriptionPreference.frequency_id.in_(non_custom_frequency_ids)).first()  # Other freqs.
    null_pref = email_prefs.filter(CandidateSubscriptionPreference.frequency_id == None).first()
    custom_frequency = Frequency.get_frequency_from_name('custom')
    custom_pref = email_prefs.filter(
        CandidateSubscriptionPreference.frequency_id == custom_frequency.id).first()  # Custom freq.
    if non_custom_pref:
        all_other_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != non_custom_pref.id)
        all_other_prefs_ids = [row.id for row in all_other_prefs]
        logger.info("get_subscription_preference: Deleting non-custom prefs for candidate %s: %s",
                                candidate_id, all_other_prefs_ids)
        db.session.query(CandidateSubscriptionPreference) \
            .filter(CandidateSubscriptionPreference.id.in_(all_other_prefs_ids)).delete(synchronize_session='fetch')
        return non_custom_pref
    elif null_pref:
        non_null_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != null_pref.id)
        non_null_prefs_ids = [row.id for row in non_null_prefs]
        logger.info("get_subscription_preference: Deleting non-null prefs for candidate %s: %s",
                                candidate_id, non_null_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
                CandidateSubscriptionPreference.id.in_(non_null_prefs_ids)).delete(synchronize_session='fetch')
        return null_pref
    elif custom_pref:
        email_prefs_ids = [row.id for row in email_prefs]
        logger.info("get_subscription_preference: Deleting all prefs for candidate %s: %s", candidate_id,
                                email_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
                CandidateSubscriptionPreference.id.in_(email_prefs_ids)).delete(synchronize_session='fetch')
        return None
