from email_campaign.common.error_handling import UnprocessableEntity

from ..models.email_marketing import EmailCampaign, EmailCampaignSmartList, EmailCampaignBlast,CandidateSubscriptionPreference,EmailCampaignSend
from common.models.user import User,Domain
from common.models.candidate import Candidate,CandidateEmail
from ..common.errors import email_notification_to_admins
from sqlalchemy import and_
from common.models.db import db
from common.models.misc import Frequency
from common.error_handling import *
from email_campaign.modules.tasks import send_scheduled_campaign
from common.talent_config import GT_ENVIRONMENT

__author__ = 'jitesh'

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

    :return: dict with newly created email_campaign_id
    """
    # If frequency is there then there must be a send time
    if frequency is not None and send_time is None:
        # 422 - Unprocessable Entity. Server understands the request but cannot process because along with frequency it needs send time.
        raise UnprocessableEntity

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
                                   # email_client_id=email_client_id,

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

    # if it's a client from api, we don't schedule campagin sends, we create it on the fly.
    # also we enable tracking by default for the clients.
    # TODO: Check if the following code is required
    # if email_client_id:
    #     campaign.update_record(isEmailOpenTracking=1,
    #                            isTrackHtmlClicks=1,
    #                            isTrackTextClicks=1)
    #
    # else:
    #     schedule_email_campaign_sends(campaign=campaign, user=user,
    #                                   email_client_id=email_client_id)

    print email_campaign
    print dir(email_campaign)

    return dict(id=email_campaign.id)


def schedule_email_campaign_sends(campaign, user, email_client_id=None, send_time=None, stop_time=None):
    """
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
    period = frequency_to_seconds(campaign.frequency.name)
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
    # request = g.request
    emails_sent = 0
    candidate_ids_and_emails = get_email_campaign_candidate_ids_and_emails(
        campaign=campaign, user=user, new_candidates_only=new_candidates_only
    )

    # Check if the smart list has more than 0 candidates
    if len(candidate_ids_and_emails) > 0:
        email_notification_to_admins(
            "Marketing email batch about to send, campaign.name=%s, user=%s, "
            "new_candidates_only=%s, address list size=%s" % (
                campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)
            ),
            subject='Marketing batch about to send'
        )
        logger.info("Marketing email batch about to send, campaign.name=%s, user=%s, "
                    "new_candidates_only=%s, address list size=%s" % (
                        campaign.name, user.email, new_candidates_only, len(candidate_ids_and_emails)))

        # Get candidates id with their email address
        candidate_ids = [id_and_email[0] for id_and_email in candidate_ids_and_emails]

        from ..common.models.candidate import Candidate

        candidates = Candidate.query.with_entities(Candidate.id, Candidate.first_name, Candidate.middle_name,
                                                   Candidate.last_name).filter_by(Candidate.id.in_(candidate_ids)).all()

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
        from datetime import datetime

        blast_datetime = datetime.now()
        email_campaign_blast_id = EmailCampaignBlast(EmailCampaignId=campaign.id,
                                                                     SentTime=blast_datetime)
        db.session.add(email_campaign_blast_id)
        blast_params = dict(sends=0, bounces=0)

        # For each candidate, create URL conversions and send the email
        for candidate_id, candidate_address in candidate_ids_and_emails:

            was_send = send_campaign_emails_to_candidate(
                user=user,
                campaign=campaign,
                candidate=candidates.find(lambda row: row.id == candidate_id).first(),
                candidate_address=candidate_address,
                blast_params=blast_params,
                email_campaign_blast_id=email_campaign_blast_id,
                blast_datetime=blast_datetime,
                email_client_id=email_client_id
            )
            db.session.commit()
            if was_send:
                emails_sent += 1

            db.session.commit()
        # So that recipients dont have to wait for all emails to be sent to read their emails. (URL conversions are stored in DB)
        # Reset sender back to normal sender
        # current.mail.settings.sender = '"getTalent Web" <no-reply@gettalent.com>'
    # flush_campaign_send_statistics_cache(user.domainId) TODO
    # TODO logging
    # logger.info("Marketing email batch completed, emails sent=%s, campaign=%s, user=%s, new_candidates_only=%s",
    #             emails_sent, campaign.name, user.email, new_candidates_only)


    return emails_sent


def get_email_campaign_candidate_ids_and_emails(campaign, user,
                                                new_candidates_only=False):
    """
    :param campaign:    email campaign row
    :param user:        user row
    :return:            Returns array of candidate IDs in the campaign's smartlists.
                        Is unique.
    """
    # Get smartlists of this campaign
    smart_lists = TalentSmartListAPI.get_from_campaign(user_id=user.id,
                                                       email_campaign_id=campaign.id)

    # Get candidate ids
    # TODO use collections.Counter class for this
    candidate_ids_dict = dict()  # Store in hash to avoid duplicate candidate ids
    for smart_list in smart_lists:
        # If the campaign is a subscription campaign,
        # only get candidates subscribed to the campaign's frequency
        if campaign.isSubscription:
            campaign_frequency_id = campaign.frequencyId
            subscribed_candidate_id_rows = db.session.query(Candidate.id).join(Candidate.candidate_subscription_preference).join(Candidate.user).filter(and_(CandidateSubscriptionPreference.frequency_id==campaign_frequency_id, User.domain_id==user.domainId)).all()
            candidate_ids = [row.id for row in subscribed_candidate_id_rows]
            if not candidate_ids:
                 logger.error("No candidates in subscription campaign %s", campaign)
        else:
             # Otherwise, just filter out unsubscribed candidates:
             # their subscription preference's frequencyId is NULL, which means 'Never'
             candidate_ids = TalentSmartListAPI.get_candidates(smart_list, candidate_ids_only=True)['candidate_ids']
             print "candidate_ids: " + str(candidate_ids)
             unsubscribed_candidate_ids = []
             for candidate_id in candidate_ids:
                  campaign_subscription_preference = get_subscription_preference(candidate_id)
                  print "campaign_subscription_preference: " + str(campaign_subscription_preference)
                  if campaign_subscription_preference and not campaign_subscription_preference.frequencyId:
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
    candidate_email_rows = CandidateEmail.query(CandidateEmail.address,CandidateEmail.candidate_id).filter(CandidateEmail.candidate_id.in_(unique_candidate_ids)).group_by(CandidateEmail.address)
     # array of (candidate id, email address) tuples
    return [(row.candidateId, row.address) for row in candidate_email_rows]


def send_campaign_emails_to_candidate(user, campaign, candidate, candidate_address,
                                      blast_params=None, email_campaign_blast_id=None,
                                      blast_datetime=None, do_email_business=None,
                                      email_client_id=None):

    """
    :param user: user row
    :param campaign: email campaign row
    :param candidate: candidate row
    """
    email_campaign_send_id = None
    try:
        # Set the email campaign blast fields if they're not defined, like if this just a test
        if not email_campaign_blast_id:
            from sqlalchemy import desc
            email_campaign_blast = EmailCampaignBlast.query.filter(EmailCampaignBlast.email_campaign_id == campaign.id).order_by(desc(EmailCampaignBlast.username)).first()
            if not email_campaign_blast:
                logger.error(
                    "send_campaign_emails_to_candidate: Must have a previous email_campaign_blast that belongs to this campaign if you don't pass in the email_campaign_blast_id param")
                return 0
            email_campaign_blast_id = email_campaign_blast.id
            blast_datetime = email_campaign_blast.sentTime
            if not blast_datetime:
                 import datetime
                 blast_datetime = datetime.datetime.now()
            if not blast_params:
                email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
                blast_params = dict(sends=email_campaign_blast.sends, bounces=email_campaign_blast.bounces)
            email_campaign_send_id =EmailCampaignSend(email_campaign_id = campaign.id, candidate_id = candidate.id, sent_time=blast_datetime)
            db.session.commit()
            # If the campaign is a subscription campaign, its body & subject are candidate-specific and will be set here
            if campaign.isSubscription:
                pass
    #             from TalentJobAlerts import get_email_campaign_fields TODO
    #             campaign_fields = get_email_campaign_fields(candidate.id, do_email_business=do_email_business)
    #             if campaign_fields['total_openings'] < 1:  # If candidate has no matching job openings, don't send the email
    #                 return 0
    #             for campaign_field_name, campaign_field_value in campaign_fields.items():
    #                 campaign[campaign_field_name] = campaign_field_value
            new_html, new_text = campaign.emailBodyHtml or "", campaign.emailBodyText or ""

            # Perform MERGETAG replacements
            [new_html, new_text, subject] = do_mergetag_replacements([new_html, new_text, campaign.emailSubject], candidate)
            # Perform URL conversions and add in the custom HTML
            new_text, new_html = create_email_campaign_url_conversions(new_html=new_html,
                                                                   new_text=new_text,
                                                                   is_track_text_clicks=campaign.isTrackTextClicks,
                                                                   is_track_html_clicks=campaign.isTrackHtmlClicks,
                                                                   custom_url_params_json=campaign.customUrlParamsJson,
                                                                   is_email_open_tracking=campaign.isEmailOpenTracking,
                                                                   custom_html=campaign.customHtml,
                                                                   email_campaign_send_id=email_campaign_send_id)
            # In dev/staging, only send emails to getTalent users, in case we're impersonating a customer.
            if GT_ENVIRONMENT in ['dev', 'qa']:
                 domain = Domain.query.get(user.domainId)
                 if 'gettalent' in domain.name.lower() or 'bluth' in domain.name.lower() or 'dice' in domain.name.lower():
                     to_addresses = user.email
                 else:
                     to_addresses = ['gettalentmailtest@gmail.com']
            else:
                to_addresses = candidate_address
            # Do not send mail if email_client_id is provided
            if email_client_id is None:
                 email_campaign_send = EmailCampaignSend.query.get(email_campaign_send_id)
                 email_response = send_email(source=campaign.emailFrom,
                                        subject=subject,
                                        html_body=new_html or None,  # Can't be '', otherwise, text_body will not show in email
                                        text_body=new_text,
                                        to_addresses=to_addresses,
                                        reply_address=campaign.emailReplyTo,  # BOTO doesn't seem to work with an array as to_addresses
                                        body=None,
                                        email_format='html' if campaign.emailBodyHtml else 'text')
            # Add activity
            # from TalentActivityAPI import TalentActivityAPI
            # activity_api = TalentActivityAPI()
            # candidate_name = candidate.name()
            # activity_api.create(user.id, activity_api.CAMPAIGN_EMAIL_SEND, source_table='email_campaign_send',
            #                 source_id=email_campaign_send_id,
            #                 params=dict(candidateId=candidate.id, campaign_name=campaign.name, candidate_name=candidate_name))

            # Save SES message ID & request ID
            logger.info("Marketing email sent to %s. Email response=%s", to_addresses, email_response)
            request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
            message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
            email_campaign_send.update_record(sesMessageId=message_id,
                                          sesRequestId=request_id)

            # Update blast
            blast_params['sends'] += 1
            EmailCampaignBlast.query.filter_by(id==email_campaign_blast_id).update(blast_params)
            db.session.commit()


    except Exception as e:
        import traceback
        # If failed to send email, still try to get request id from XML response.
        # Unfortunately XML response is malformed so must manually parse out request id
        # Also, mark email as bounced
        import re
        request_id_search = re.search('<RequestId>(.*)</RequestId>', e.__str__(), re.IGNORECASE)
        request_id = request_id_search.group(1) if request_id_search else None
        EmailCampaignSend.query.fiter(email_campaign_send_id==email_campaign_send_id).update(isSesBounce=1, sesRequestId=request_id)
        # Update blast
        blast_params['bounces'] += 1
        EmailCampaignBlast.query.filter(id== email_campaign_blast_id).update(blast_params)
        # Send failure message to email marketing admin, just to notify for verification
        logger.exception("Failed to send marketing email to candidate_id=%s, candidate_address=%s", candidate.id,
                         candidate_address)
        return 0
    return 1

