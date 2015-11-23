import datetime
import re

from flask import current_app
from sqlalchemy import and_
from sqlalchemy import desc
from email_campaign.common.models.db import db
from email_campaign.common.models.email_marketing import EmailCampaign, EmailCampaignSmartList, EmailCampaignBlast, \
    CandidateSubscriptionPreference, EmailCampaignSend
from email_campaign.common.models.misc import Frequency
from email_campaign.common.models.user import User, Domain
from email_campaign.common.models.candidate import Candidate, CandidateEmail
from email_campaign.common.error_handling import *
from email_campaign.common.emails.admin_reporting import email_admins
from email_campaign.common.emails.AWS_SES import send_email
from email_campaign.modules.utils import create_email_campaign_url_conversions, do_mergetag_replacements, get_candidates

__author__ = 'jitesh'


def create_email_campaign_smart_lists(smart_list_ids, email_campaign_id):
    """ Maps smart lists to email campaign
    :param smart_list_ids:
    :type smart_list_ids: list[int | long]
    :param email_campaign_id: id of email campaign to which smart lists will be associated.

    """
    if type(smart_list_ids) in (int, long):
        smart_list_ids = [smart_list_ids]
    for smart_list_id in smart_list_ids:
        email_campaign_smart_list = EmailCampaignSmartList(smart_list_id=smart_list_id,
                                                           email_campaign_id=email_campaign_id)
        db.session.add(email_campaign_smart_list)


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

    # TODO: Add activity

    # create email_campaign_smart_list record
    create_email_campaign_smart_lists(smart_list_ids=list_ids,
                                      email_campaign_id=email_campaign.id)

    db.session.commit()

    # if it's a client from api, we don't schedule campaign sends, we create it on the fly.
    # also we enable tracking by default for the clients.
    if email_client_id:
        email_campaign.isEmailOpenTracking = 1
        email_campaign.isTrackHtmlClicks = 1
        email_campaign.isTrackTextClicks = 1
        db.session.commit()

    # TODO: Schedule the sending of emails & update email_campaign_send fields
    # else:
    #     schedule_email_campaign_sends(campaign=campaign, user=user,
    #                                   email_client_id=email_client_id)

    user = User.query.get(user_id)
    send_emails_to_campaign(oauth_token, email_campaign, user, email_client_id, list_ids)
    return dict(id=email_campaign.id)


def send_emails_to_campaign(oauth_token, campaign, user, email_client_id=None, list_ids=None, new_candidates_only=False):
    """
    new_candidates_only sends the emails only to candidates who haven't yet
    received any as part of this campaign.

    :param campaign:    email campaign row
    :param user:        user row
    :return:            number of emails sent
    """
    emails_sent = 0
    candidate_ids_and_emails = get_email_campaign_candidate_ids_and_emails(oauth_token, campaign=campaign, user=user, list_ids=list_ids,
                                                                           new_candidates_only=new_candidates_only)

    # Check if the smart list has more than 0 candidates
    if len(candidate_ids_and_emails) > 0:
        email_admins(
            env=current_app.config['GT_ENVIRONMENT'],
            subject='Marketing batch about to send',
            body="Marketing email batch about to send, campaign.name=%s, user=%s, \
        new_candidates_only=%s, address list size=%s" % (
                campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)
            )
        )
        current_app.logger.info("Marketing email batch about to send, campaign.name=%s, user=%s, "
                                "new_candidates_only=%s, address list size=%s" % (
                                    campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)))

        # TODO: Add activity

        # Create the email_campaign_blast for this blast
        blast_datetime = datetime.datetime.now()
        email_campaign_blast = EmailCampaignBlast(email_campaign_id=campaign.id, sent_time=blast_datetime)
        db.session.add(email_campaign_blast)
        db.session.commit()
        blast_params = dict(sends=0, bounces=0)

        # For each candidate, create URL conversions and send the email
        for candidate_id, candidate_address in candidate_ids_and_emails:

            was_send = send_campaign_emails_to_candidate(
                user=user,
                campaign=campaign,
                candidate=Candidate.query.get(candidate_id),  #candidates.find(lambda row: row.id == candidate_id).first(),
                candidate_address=candidate_address,
                blast_params=blast_params,
                email_campaign_blast_id=email_campaign_blast.id,
                blast_datetime=blast_datetime,
                email_client_id=email_client_id
            )
            # db.session.commit()
            if was_send:
                emails_sent += 1

            db.session.commit()
    current_app.logger.info(
        "Marketing email batch completed, emails sent=%s, campaign=%s, user=%s, new_candidates_only=%s", emails_sent,
        campaign.name, user.email, new_candidates_only)

    return emails_sent


def get_email_campaign_candidate_ids_and_emails(oauth_token, campaign, user, list_ids=None,
                                                new_candidates_only=False):
    """
    :param campaign:    email campaign row
    :param user:        user row
    :return:            Returns array of candidate IDs in the campaign's smartlists.
                        Is unique.
    """
    if list_ids is None:
        # Get smartlists of this campaign
        list_ids = db.session.query(EmailCampaignSmartList.smart_list_id).filter_by(email_campaign_id=campaign.id).all()
        list_ids = [list_id[0] for list_id in list_ids]
    # Get candidate ids
    candidate_ids_dict = dict()  # Store in hash to avoid duplicate candidate ids
    for list_id in list_ids:
        # If the campaign is a subscription campaign,
        # only get candidates subscribed to the campaign's frequency
        if campaign.is_subscription:
            campaign_frequency_id = campaign.frequency_id
            subscribed_candidate_id_rows = db.session.query(Candidate.id)\
                .join(CandidateSubscriptionPreference, Candidate.id == CandidateSubscriptionPreference.candidate_id)\
                .join(User, Candidate.user_id == User.id)\
                .filter(and_(CandidateSubscriptionPreference.frequency_id == campaign_frequency_id,
                             User.domain_id == user.domain_id)).all()
            candidate_ids = [row.id for row in subscribed_candidate_id_rows]
            if not candidate_ids:
                current_app.logger.error("No candidates in subscription campaign %s", campaign)
        else:
            # Otherwise, just filter out unsubscribed candidates:
            # their subscription preference's frequencyId is NULL, which means 'Never'
            candidate_ids = get_candidates(oauth_token, list_id, candidate_ids_only=True)
            current_app.logger.debug("candidate_ids: %s" % candidate_ids)
            unsubscribed_candidate_ids = []
            for candidate_id in candidate_ids:
                campaign_subscription_preference = get_subscription_preference(candidate_id)
                current_app.logger.debug("campaign_subscription_preference: %s" % campaign_subscription_preference)
                if campaign_subscription_preference and not campaign_subscription_preference.frequency_id:
                    unsubscribed_candidate_ids.append(candidate_id)
            for unsubscribed_candidate_id in unsubscribed_candidate_ids:
                if unsubscribed_candidate_id in candidate_ids:
                    candidate_ids.remove(unsubscribed_candidate_id)
        # If only getting candidates that haven't been emailed before...
        if new_candidates_only:
            emailed_candidate_ids = db.session.query(EmailCampaignSend).filter(
                EmailCampaignSend.email_campaign_id == campaign.id).group_by(EmailCampaignSend.candidate_id).all()
            emailed_candidate_ids_dict = dict( emailed_candidate_ids)
            for candidate_id in candidate_ids:
                if not candidate_ids_dict.get(candidate_id) and not emailed_candidate_ids_dict.get(candidate_id):
                    candidate_ids_dict[candidate_id] = True
        else:
            for candidate_id in candidate_ids:
                if not candidate_ids_dict.get(candidate_id):
                    candidate_ids_dict[candidate_id] = True
    unique_candidate_ids = candidate_ids_dict.keys()
     # Get emails
    candidate_email_rows = db.session.query(CandidateEmail.candidate_id, CandidateEmail.address)\
        .filter(CandidateEmail.candidate_id.in_(unique_candidate_ids))\
        .group_by(CandidateEmail.address)
     # array of (candidate id, email address) tuples
    return [(row.candidate_id, row.address) for row in candidate_email_rows]


def send_campaign_emails_to_candidate(user, campaign, candidate, candidate_address,
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
        email_campaign_blast = EmailCampaignBlast.query.filter(EmailCampaignBlast.email_campaign_id == campaign.id).order_by(desc(EmailCampaignBlast.sent_time)).first()
        if not email_campaign_blast:
            current_app.logger.error(
                "send_campaign_emails_to_candidate: Must have a previous email_campaign_blast that belongs to this campaign if you don't pass in the email_campaign_blast_id param")
            return 0
        email_campaign_blast_id = email_campaign_blast.id
        blast_datetime = email_campaign_blast.sentTime
    if not blast_datetime:
        blast_datetime = datetime.datetime.now()
    if not blast_params:
        email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
        blast_params = dict(sends=email_campaign_blast.sends, bounces=email_campaign_blast.bounces)
    email_campaign_send = EmailCampaignSend(email_campaign_id=campaign.id, candidate_id=candidate.id, sent_time=blast_datetime)
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
    # In dev/staging, only send emails to getTalent users, in case we're impersonating a customer.
    if current_app.config['GT_ENVIRONMENT'] in ['dev', 'qa', 'circle']:
        domain = Domain.query.get(user.domain_id)
        if 'gettalent' in domain.name.lower() or 'bluth' in domain.name.lower() or 'dice' in domain.name.lower():
            to_addresses = user.email
        else:
            to_addresses = ['gettalentmailtest@gmail.com']
    else:
        to_addresses = candidate_address
    # Do not send mail if email_client_id is provided
    if email_client_id:
        current_app.logger.info("Marketing email added through client %s", email_client_id)
        # TODO: Add activity
        return new_html, new_text
    else:
        try:
            email_response = send_email(source=campaign.email_from,
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
            return 0
        # Save SES message ID & request ID
        current_app.logger.info("Marketing email sent to %s. Email response=%s", to_addresses, email_response)
        request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
        message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
        email_campaign_send.ses_message_id=message_id
        email_campaign_send.ses_request_id=request_id
        db.session.commit()
    # TODO: Add activity

    # Update blast
    blast_params['sends'] += 1
    email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
    email_campaign_blast.sends = blast_params['sends']
    db.session.commit()

    return 1


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
    current_app.logger.exception(
        "Failed to send marketing email to candidate_id=%s, to_addresses=%s" % (candidate.id, to_addresses))


def get_subscription_preference(candidate_id):
    """
    If there are multiple subscription preferences (due to legacy reasons),
    if any one is 1-6, keep it and delete the rest.
    Otherwise, if any one is NULL, keep it and delete the rest.
    Otherwise, if any one is 7, delete all of them.
    """
    # TODO: Ask about this function? Can this be modified and create other script to delete legacy data on all domains.
    # email_prefs = db(db.candidate_subscription_preference.candidateId == candidate_id).select()
    email_prefs = db.session.query(CandidateSubscriptionPreference).filter_by(candidate_id=candidate_id)
    non_custom_frequencies = db.session.query(Frequency.id).filter(Frequency.name.in_(Frequency.standard_frequencies().keys())).all()
    non_custom_frequency_ids = [non_custom_frequency[0] for non_custom_frequency in non_custom_frequencies]
    non_custom_pref = email_prefs.filter(CandidateSubscriptionPreference.frequency_id.in_(non_custom_frequency_ids)).first()  # Other freqs.
    null_pref = email_prefs.filter(CandidateSubscriptionPreference.frequency_id == None).first()
    custom_frequency = Frequency.get_frequency_from_name('custom')
    custom_pref = email_prefs.filter(CandidateSubscriptionPreference.frequency_id == custom_frequency.id).first()  # Custom freq.
    if non_custom_pref:
        all_other_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != non_custom_pref.id)
        all_other_prefs_ids = [row.id for row in all_other_prefs]
        current_app.logger.info("get_subscription_preference: Deleting non-custom prefs for candidate %s: %s",
                                candidate_id, all_other_prefs_ids)
        db.session.query(CandidateSubscriptionPreference)\
            .filter(CandidateSubscriptionPreference.id.in_(all_other_prefs_ids)).delete(synchronize_session='fetch')
        return non_custom_pref
    elif null_pref:
        non_null_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != null_pref.id)
        non_null_prefs_ids = [row.id for row in non_null_prefs]
        current_app.logger.info("get_subscription_preference: Deleting non-null prefs for candidate %s: %s",
                                candidate_id, non_null_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
            CandidateSubscriptionPreference.id.in_(non_null_prefs_ids)).delete(synchronize_session='fetch')
        return null_pref
    elif custom_pref:
        email_prefs_ids = [row.id for row in email_prefs]
        current_app.logger.info("get_subscription_preference: Deleting all prefs for candidate %s: %s", candidate_id, email_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
            CandidateSubscriptionPreference.id.in_(email_prefs_ids)).delete(synchronize_session='fetch')
        return None
