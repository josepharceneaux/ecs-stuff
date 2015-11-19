import datetime
import json
import re

from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit
from flask import current_app
from BeautifulSoup import BeautifulSoup, Tag
from common.talent_config import GT_ENVIRONMENT
from sqlalchemy import and_
from sqlalchemy import desc
from common.models.db import db
from common.models.email_marketing import EmailCampaign, EmailCampaignSmartList, EmailCampaignBlast, \
    CandidateSubscriptionPreference, EmailCampaignSend, UrlConversion, EmailCampaignSendUrlConversion
from common.models.misc import Frequency
from common.models.user import User, Domain
from common.models.candidate import Candidate, CandidateEmail
from common.models.smart_list import SmartList, SmartListCandidate
from common.error_handling import *
from email_campaign.common.error_handling import UnprocessableEntity
from email_campaign.modules.tasks import send_scheduled_campaign
from common.emails.admin_reporting import email_admins
from common.emails.AWS_SES import send_email

__author__ = 'jitesh'

DEFAULT_FIRST_NAME_MERGETAG = "*|FIRSTNAME|*"
DEFAULT_LAST_NAME_MERGETAG = "*|LASTNAME|*"
DEFAULT_PREFERENCES_URL_MERGETAG = "*|PREFERENCES_URL|*"
HTML_CLICK_URL_TYPE = 2
TRACKING_URL_TYPE = 0


def validate_lists_belongs_to_domain(list_ids, user_id):
    """

    :param list_ids:
    :param user_id:
    :return:False, if any of list given not belongs to current user domain else True
    """
    user = User.query.get(user_id)
    smart_lists = db.session.query(SmartList.id).join(User, SmartList.user_id == User.id).filter(User.domain_id==user.domain_id).all()

    smart_list_ids = [smart_list[0] for smart_list in smart_lists]
    result_of_list_belong_domain = set(list_ids) - set(smart_list_ids)
    if len(result_of_list_belong_domain) == 0:
        return True
    return False


def _create_email_campaign_smart_lists(smart_list_ids, email_campaign_id):
    """ Maps smart lists to email campaign
    :param smart_list_ids:
    :type smart_list_ids: list[int | long]
    :param email_campaign_id: id of email campaign to which smart lists will be associated.
    :return:
    """
    if type(smart_list_ids) in (int, long):
        smart_list_ids = [smart_list_ids]
    for smart_list_id in smart_list_ids:
        email_campaign_smart_list = EmailCampaignSmartList(smart_list_id=smart_list_id,
                                                           email_campaign_id=email_campaign_id)
        db.session.add(email_campaign_smart_list)


def _send_campaign_emails(campaign, user, new_candidates_only):
    # Get all candidates associated with smartlists
    # Mail admins notifying the start of email campaign. (if the smart list has more than 0 candidates)
    candidate_ids_and_emails = 0  # TODO
    email_admins(
        env=GT_ENVIRONMENT,
        subject='Marketing batch about to send',
        body="Marketing email batch about to send, campaign.name=%s, user=%s, \
        new_candidates_only=%s, address list size=%s" % (
            campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)
        )
    )
    # Add activity email campaign send
    # Create the email_campaign_blast for this blast
    email_campaign_blast = EmailCampaignBlast(email_campaign_id=campaign.id, sent_time=datetime.datetime.now())
    db.session.add(email_campaign_blast)
    blast_params = {'sends': 0, 'bounces': 0}
    # For each candidate, create URL conversions and send the email


def create_email_campaign(user_id, email_campaign_name, email_subject,
                          email_from, email_reply_to, email_body_html,
                          email_body_text, list_ids, email_client_id=None,
                          frequency=None,
                          send_time=None,
                          stop_time=None,
                          template_id=None):
    """
    Creates a new email campaign.
    Schedules email campaign.
    Creates email campaign send.

    :return: newly created email_campaign's id
    """
    # If frequency is there then there must be a send time
    if frequency is not None and send_time is None:
        # 422 - Unprocessable Entity. Server understands the request but cannot process
        # because along with frequency it needs send time.
        # https://tools.ietf.org/html/rfc4918#section-11.2
        # 400 or 422? Will decide it later.
        raise UnprocessableEntity("Frequency requires send time.")

    # Case insensitive filter
    frequency_obj = db.session.query(Frequency).filter(Frequency.name == frequency).first() if frequency else None

    email_campaign = EmailCampaign(user_id=user_id,
                                   name=email_campaign_name,
                                   is_hidden=0,
                                   email_subject=email_subject,
                                   email_from=email_from,
                                   email_reply_to=email_reply_to,
                                   email_body_html=email_body_html,
                                   email_body_text=email_body_text,
                                   frequency_id=frequency_obj.id if frequency_obj else None,
                                   email_client_id=email_client_id,

                                   send_time=send_time)

    db.session.add(email_campaign)
    db.session.commit()

    # TODO: Add activity
    # activity_api.create(user_id, activity_api.CAMPAIGN_CREATE,
    #                     source_table='email_campaign',
    #                     source_id=email_campaign_id,
    #                     params=dict(id=email_campaign_id,
    #                                 name=email_campaign_name))

    # Make email_campaign_smart_list records
    _create_email_campaign_smart_lists(smart_list_ids=list_ids,
                                       email_campaign_id=email_campaign.id)

    db.session.commit()

    # Schedule the sending of emails & update email_campaign_send fields
    # campaign = db.email_campaign(email_campaign_id)
    # campaign = EmailCampaign.query.get(email_campaign.id)

    # if it's a client from api, we don't schedule campaign sends, we create it on the fly.
    # also we enable tracking by default for the clients.
    # TODO: Check if the following code is required
    if email_client_id:
        email_campaign.isEmailOpenTracking = 1
        email_campaign.isTrackHtmlClicks = 1
        email_campaign.isTrackTextClicks = 1
        db.session.commit()

    # else:
    #     schedule_email_campaign_sends(campaign=campaign, user=user,
    #                                   email_client_id=email_client_id)

    user = User.query.get(user_id)
    send_emails_to_campaign(email_campaign, user, email_client_id)
    return dict(id=email_campaign.id)


def schedule_email_campaign_sends(campaign, user, email_client_id=None, send_time=None, stop_time=None):
    """
    NOT USED
    :param campaign:            email_campaign row
    :param user:                user row
    :param email_client_id:     email client's unique id,
                                which references the source of the email client
    """
    # repeats = 0 means unlimited
    repeats = 0
    start_time = send_time if send_time else campaign.sendTime
    stop_time = stop_time if stop_time else campaign.stopTime

    if campaign.frequency.id == 1:
        repeats = 1
    period = campaign.frequency.in_seconds
    function_vars = dict(campaign_id=campaign.id, user_id=user.id,
                         email_client_id=email_client_id)

    if period == 0:
        # Celery task run now (as soon as worker is free)
        send_scheduled_campaign.delay(function_vars)
    # If campaign to be sent in future
    # scheduler_task_id = schedule_task(function_name='email_campaign_scheduled',
    #                                   function_vars=function_vars,
    #                                   start_time=start_time,
    #                                   stop_time=stop_time,
    #                                   period=period, repeats=repeats)
    # campaign.update_record(schedulerTaskIds=[scheduler_task_id])


def frequency_to_seconds(frequency_name):
    """ Get frequency name from given frequency id and converts it into seconds
    Frequency other then below mentioned names will return 0 seconds.
    'Once', 'Daily', 'Weekly', 'Biweekly', 'Monthly', 'Yearly'
    :param frequency_name:
    :return:frequency in seconds
    """
    frequency_name = frequency_name.lower()
    frequency_in_seconds = {'once': 0, 'daily': 24 * 3600, 'weekly': 7 * 24 * 3600, 'biweekly': 2 * 7 * 24 * 3600,
                            'monthly': 30 * 24 * 3600, 'yearly': 365 * 24 * 3600}
    if frequency_name not in frequency_in_seconds.keys():
        # For unknown frequency names return 0 seconds.
        # Log error TODO
        return 0
    return frequency_in_seconds.get(frequency_name, 0)

    # if not frequency_id or frequency_id == 1:
    #     period = 0
    # elif frequency_id == 2:
    #     period = 24 * 3600
    # elif frequency_id == 3:
    #     period = 7 * 24 * 3600
    # elif frequency_id == 4:
    #     period = 14 * 24 * 3600
    # elif frequency_id == 5:
    #     period = 30 * 24 * 3600
    # elif frequency_id == 6:
    #     period = 365 * 24 * 3600
    # else:
    #     current.logger.error("Unknown number of seconds for frequency ID: %s", frequency_id)
    #     period = 0
    #
    # return period


def send_emails_to_campaign(campaign, user, email_client_id=None, new_candidates_only=False):
    """
    new_candidates_only sends the emails only to candidates who haven't yet
    received any as part of this campaign.

    :param campaign:    email campaign row
    :param user:        user row
    :return:            number of emails sent
    """
    emails_sent = 0
    candidate_ids_and_emails = get_email_campaign_candidate_ids_and_emails(
        campaign=campaign, user=user, new_candidates_only=new_candidates_only
    )

    # Check if the smart list has more than 0 candidates
    if len(candidate_ids_and_emails) > 0:
        email_admins(
            env=GT_ENVIRONMENT,
            subject='Marketing batch about to send',
            body="Marketing email batch about to send, campaign.name=%s, user=%s, \
        new_candidates_only=%s, address list size=%s" % (
                campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)
            )
        )
        current_app.logger.info("Marketing email batch about to send, campaign.name=%s, user=%s, "
                                "new_candidates_only=%s, address list size=%s" % (
                                    campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)))

        # Get candidates id with their email address
        # candidate_ids = [id_and_email[0] for id_and_email in candidate_ids_and_emails]

        # candidates = db.session.query(Candidate.id).filter_by(Candidate.id.in_(candidate_ids)).all()

        # Add activity
        #  from TalentActivityAPI import TalentActivityAPI
        #  activity_api = TalentActivityAPI()
        #  activity_api.create(
        #     user.id,
        #     activity_api.CAMPAIGN_SEND,
        #     source_table='email_campaign',
        #     source_id=campaign.id,
        #     params=dict(
        #         id=campaign.id,
        #         name=campaign.name,
        #         num_candidates=len(candidate_ids)
        #     )
        # )

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
        # So that recipients dont have to wait for all emails to be sent to read their emails. (URL conversions are stored in DB)
        # Reset sender back to normal sender
        # current.mail.settings.sender = '"getTalent Web" <no-reply@gettalent.com>'
    current_app.logger.info(
        "Marketing email batch completed, emails sent=%s, campaign=%s, user=%s, new_candidates_only=%s", emails_sent,
        campaign.name, user.email, new_candidates_only)

    return emails_sent


def get_email_campaign_candidate_ids_and_emails(campaign, user, list_ids=None,
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
            # subscribed_candidate_id_rows = db.session.query(Candidate.id).join(Candidate.candidate_subscription_preference).join(Candidate.user).filter(and_(CandidateSubscriptionPreference.frequency_id==campaign_frequency_id, User.domain_id==user.domainId)).all()
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
            candidate_ids = get_candidates(list_id, candidate_ids_only=True)['candidate_ids']
            print "candidate_ids: " + str(candidate_ids)
            unsubscribed_candidate_ids = []
            for candidate_id in candidate_ids:
                campaign_subscription_preference = get_subscription_preference(candidate_id)
                print "campaign_subscription_preference: " + str(campaign_subscription_preference)
                if campaign_subscription_preference and not campaign_subscription_preference.frequency_id:
                    unsubscribed_candidate_ids.append(candidate_id)
            for unsubscribed_candidate_id in unsubscribed_candidate_ids:
                if unsubscribed_candidate_id in candidate_ids:
                    candidate_ids.remove(unsubscribed_candidate_id)
        # If only getting candidates that haven't been emailed before...
        if new_candidates_only:
            emailed_candidate_ids = EmailCampaignSend.query.filter(EmailCampaignSend.email_campaign_id==campaign.id).group_by(EmailCampaignSend.candidate_id).all()
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
    if GT_ENVIRONMENT in ['deva', 'qa']:
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
        # TODO: Add activity required?
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
    # Add activity
    # from TalentActivityAPI import TalentActivityAPI
    # activity_api = TalentActivityAPI()
    # candidate_name = candidate.name()
    # activity_api.create(user.id, activity_api.CAMPAIGN_EMAIL_SEND, source_table='email_campaign_send',
    #                 source_id=email_campaign_send_id,
    #                 params=dict(candidateId=candidate.id, campaign_name=campaign.name, candidate_name=candidate_name))

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


def do_mergetag_replacements(texts, candidate=None):
    """
    If no candidate, name is "John Doe"
    """
    first_name = "John"
    last_name = "Doe"
    if candidate:
        first_name = candidate.first_name if candidate.first_name else "John"
        last_name = candidate.last_name if candidate.last_name else "Doe"

    new_texts = []
    for text in texts:
        # Do first/last name replacements
        text = text.replace(DEFAULT_FIRST_NAME_MERGETAG, first_name) if text and (
            DEFAULT_FIRST_NAME_MERGETAG in text) else text
        text = text.replace(DEFAULT_LAST_NAME_MERGETAG, last_name) if text and (
            DEFAULT_LAST_NAME_MERGETAG in text) else text

        # Do 'Unsubscribe' link replacements
        if candidate and text and (DEFAULT_PREFERENCES_URL_MERGETAG in text):
            text = do_prefs_url_replacement(text, candidate.id)

        new_texts.append(text)

    return new_texts


def do_prefs_url_replacement(text, candidate_id):
    unsubscribe_url = 'http://localhost:8007/unsubscribe'
    # TODO: check for unsubscribe url
    # unsubscribe_url = current.HOST_NAME + URL(scheme=False, host=False, a='web',
    #                                           c='candidate', f='prefs',
    #                                           args=[candidate_id],
    #                                           hmac_key=current.HMAC_KEY)

    # In case the user accidentally wrote http://*|PREFERENCES_URL|* or https://*|PREFERENCES_URL|*
    text = text.replace("http://" + DEFAULT_PREFERENCES_URL_MERGETAG, unsubscribe_url)
    text = text.replace("https://" + DEFAULT_PREFERENCES_URL_MERGETAG, unsubscribe_url)

    # The normal case
    text = text.replace(DEFAULT_PREFERENCES_URL_MERGETAG, unsubscribe_url)
    return text


def set_query_parameters(url, param_dict):
    """
    Given a URL, set or replace a query parameter and return the modified URL.
    Taken & modified from:
    http://stackoverflow.com/questions/4293460/how-to-add-custom-parameters-to-an-url-query-string-with-python

    :param url:
    :param param_dict:
    :return:
    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)

    for param_name, param_value in param_dict.items():
        if not query_params.get(param_name):
            query_params[param_name] = []
        query_params[param_name].append(param_value)

    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


def create_email_campaign_url_conversion(destination_url, email_campaign_send_id,
                                         type_, destination_url_custom_params=None):
    """
    Creates url_conversion in DB and returns source url
    """

    # Insert url_conversion
    if destination_url_custom_params:
        destination_url = set_query_parameters(destination_url, destination_url_custom_params)

    # source_url = current.HOST_NAME + str(URL(a='web', c='default', f='url_redirect', args=url_conversion_id, hmac_key=current.HMAC_KEY))
    source_url = 'http://localhost:8007/source_url'  # TODO
    url_conversion = UrlConversion(destination_url=destination_url, source_url=source_url)
    db.session.add(url_conversion)
    db.session.commit()
    # Insert email_campaign_send_url_conversion
    EmailCampaignSendUrlConversion(email_campaign_send_id=email_campaign_send_id, url_conversion_id=url_conversion.id,
                                   type=type_)
    return source_url


def create_email_campaign_url_conversions(new_html, new_text, is_track_text_clicks,
                                          is_track_html_clicks, custom_url_params_json,
                                          is_email_open_tracking, custom_html,
                                          email_campaign_send_id):
    soup = None

    # HTML open tracking
    if new_html and is_email_open_tracking:
        soup = BeautifulSoup(new_html)
        num_conversions = convert_html_tag_attributes(
            soup,
            lambda url: create_email_campaign_url_conversion(url, email_campaign_send_id, TRACKING_URL_TYPE),
            tag="img",
            attribute="src",
            convert_first_only=True
        )

        # If no images found, add a tracking pixel
        if not num_conversions:
            # image_url = URL('static', 'images/pixel.png', host=True)
            image_url = "http://localhost:8007/images/pixel.png"
            new_image_url = create_email_campaign_url_conversion(image_url, email_campaign_send_id, TRACKING_URL_TYPE)
            new_image_tag = Tag(soup, "img", [("src", new_image_url)])
            soup.insert(0, new_image_tag)

    # HTML click tracking
    if new_html and is_track_html_clicks:
        soup = soup or BeautifulSoup(new_html)

        # Fetch the custom URL params dict, if any
        if custom_url_params_json:

            destination_url_custom_params = json.loads(custom_url_params_json)
        else:
            destination_url_custom_params = dict()

        # Convert all of soup's <a href=> attributes

        convert_html_tag_attributes(
            soup,
            lambda url: create_email_campaign_url_conversion(url,
                                                             email_campaign_send_id,
                                                             HTML_CLICK_URL_TYPE,
                                                             destination_url_custom_params),
            tag="a",
            attribute="href"
        )

    # Add custom HTML. Doesn't technically belong in this function, but since we have access to the BeautifulSoup object, let's do it here.
    if new_html and custom_html:
        soup = soup or BeautifulSoup(new_html)
        body_tag = soup.find(name="body") or soup.find(name="html")
        """
        :type: Tag | None
        """
        if body_tag:
            custom_html_soup = BeautifulSoup(custom_html)
            body_tag.insert(0, custom_html_soup)
        else:
            current_app.logger.error("Email campaign HTML did not have a body or html tag, "
                                     "so couldn't insert custom_html! email_campaign_send_id=%s",
                                     email_campaign_send_id)

    # Convert soup object into new HTML
    if new_html and soup:
        new_html = soup.prettify()

    return new_text, new_html


def convert_html_tag_attributes(soup, conversion_function, tag="a",
                                attribute="href", convert_first_only=False):
    """
    Takes in BeautifulSoup object and calls conversion_function on every given
    attribute of given tag.

    :return:    Number of conversions done. (BeautifulSoup object is modified.)
    """
    items = soup.findAll(tag)
    replacements = 0
    for item in items:
        if item[attribute]:
            item[attribute] = conversion_function(item[attribute])
            replacements += 1
            if convert_first_only: break
    return replacements


def get_candidates(list_id, candidate_ids_only=False, count_only=False, max_candidates=0):
    """
    Gets the candidates of a smart or dumb list.

    :param max_candidates: If set to 0, will have no limit.
    :return:  dict of 'candidate_ids, total_found' if candidate_ids_only=True, otherwise returns
    what TalentSearch.search_candidates returns
    """
    smart_list = SmartList.query.get(list_id)
    domain_id = smart_list.user.domain_id

    # If it is a smartlist, perform the dynamic search
    if smart_list.search_params:
        search_params = json.loads(smart_list.search_params)
        # TODO: Get candidates from candidate search service
        search_results = search_candidates(domainId=domain_id, vars=search_params, search_limit=max_candidates,
                                           candidate_ids_only=candidate_ids_only,
                                           count_only=count_only)  # returns total_found, candidate_ids
    # If a dumblist & getting count only, just do count
    elif count_only:
        count = db.session.query(SmartListCandidate.candidate_id).filter_by(smart_list_id=smart_list.id).count()
        search_results = dict(candidate_ids=[], total_found=count)
    # If a dumblist and not doing count only, simply return all smart_list_candidates
    else:
        smart_list_candidate_rows = db.session.query(SmartListCandidate.candidate_id)\
            .filter_by(smart_list_id=smart_list.id)
        if max_candidates:
            smart_list_candidate_rows = smart_list_candidate_rows.limit(max_candidates)
            # count = get_candidates(smart_list, candidate_ids_only=candidate_ids_only, count_only=True)['total_found']

        count = smart_list_candidate_rows.count()
        candidate_ids = [smart_list_candidate_row.candidate_id for smart_list_candidate_row in smart_list_candidate_rows]

        search_results = dict(candidate_ids=candidate_ids, total_found=count)
    print "get_candidates_result: " + str(search_results)
    return search_results


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
        # db(db.candidate_subscription_preference.id.belongs(all_other_prefs_ids)).delete()
        return non_custom_pref
    elif null_pref:
        non_null_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != null_pref.id)
        non_null_prefs_ids = [row.id for row in non_null_prefs]
        current_app.logger.info("get_subscription_preference: Deleting non-null prefs for candidate %s: %s",
                                candidate_id, non_null_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
            CandidateSubscriptionPreference.id.in_(non_null_prefs_ids)).delete(synchronize_session='fetch')
        # db(db.candidate_subscription_preference.id.belongs(non_null_prefs_id)).delete()
        return null_pref
    elif custom_pref:
        email_prefs_ids = [row.id for row in email_prefs]
        current_app.logger.info("get_subscription_preference: Deleting all prefs for candidate %s: %s", candidate_id, email_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
            CandidateSubscriptionPreference.id.in_(email_prefs_ids)).delete(synchronize_session='fetch')
        # db(db.candidate_subscription_preference.id.belongs(email_prefs_ids)).delete()
        return None
