"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains function used by email-campaign-api.
"""
# Standard Imports
import re
import json
import datetime
import itertools

# Third Party
from celery import chord
from sqlalchemy import and_, desc

# Service Specific
from email_campaign_service.modules.validations import get_or_set_valid_value
from email_campaign_service.email_campaign_app import (logger, celery_app, app)
from email_campaign_service.modules.utils import (TRACKING_URL_TYPE,
                                                  get_candidates_from_smartlist,
                                                  do_mergetag_replacements,
                                                  create_email_campaign_url_conversions, AWS_SNS_TERMS)

# Common Utils
from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.user import User
from email_campaign_service.common.models.user import Domain
from email_campaign_service.common.utils.amazon_ses import send_email
from email_campaign_service.common.models.misc import (Frequency, Activity)
from email_campaign_service.common.utils.scheduler_utils import SchedulerUtils
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.routes import SchedulerApiUrl, EmailCampaignUrl
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.campaign_services.custom_errors import CampaignException
from email_campaign_service.common.models.email_campaign import (EmailCampaign,
                                                                 EmailCampaignSmartlist,
                                                                 EmailCampaignBlast,
                                                                 EmailCampaignSend,
                                                                 EmailCampaignSendUrlConversion)
from email_campaign_service.common.utils.handy_functions import (http_request,
                                                                 JSON_CONTENT_TYPE_HEADER)
from email_campaign_service.common.models.candidate import (Candidate, CandidateEmail,
                                                            CandidateSubscriptionPreference, EmailLabel)
from email_campaign_service.common.error_handling import (InvalidUsage, InternalServerError)
from email_campaign_service.common.utils.talent_reporting import email_notification_to_admins
from email_campaign_service.common.inter_service_calls.candidate_service_calls import \
    get_candidate_subscription_preference
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import get_candidates_of_smartlist


def create_email_campaign_smartlists(smartlist_ids, email_campaign_id):
    """ Maps smart lists to email campaign
    :param smartlist_ids:
    :type smartlist_ids: list[int | long]
    :param email_campaign_id: id of email campaign to which smart lists will be associated.

    """
    if type(smartlist_ids) in (int, long):
        smartlist_ids = [smartlist_ids]
    for smartlist_id in smartlist_ids:
        email_campaign_smartlist = EmailCampaignSmartlist(smartlist_id=smartlist_id,
                                                          campaign_id=email_campaign_id)
        db.session.add(email_campaign_smartlist)
    db.session.commit()


def create_email_campaign(user_id, oauth_token, name, subject,
                          _from, reply_to, body_html,
                          body_text, list_ids, email_client_id=None,
                          frequency_id=None,
                          start_datetime=None,
                          end_datetime=None,
                          template_id=None):
    """
    Creates a new email campaign.
    Schedules email campaign.

    :return: newly created email_campaign's id
    """
    frequency = Frequency.get_seconds_from_id(frequency_id)
    email_campaign = EmailCampaign(name=name,
                                   user_id=user_id,
                                   is_hidden=0,
                                   subject=subject,
                                   _from=get_or_set_valid_value(_from, basestring, '').strip(),
                                   reply_to=get_or_set_valid_value(reply_to, basestring, '').strip(),
                                   body_html=body_html,
                                   body_text=body_text,
                                   start_datetime=start_datetime,
                                   end_datetime=end_datetime,
                                   frequency_id=frequency_id if frequency_id else None,
                                   email_client_id=email_client_id
                                   )
    EmailCampaign.save(email_campaign)

    try:
        # Add activity
        CampaignBase.create_activity(user_id,
                                     Activity.MessageIds.CAMPAIGN_CREATE,
                                     email_campaign,
                                     dict(id=email_campaign.id,
                                          name=name))
    except Exception:
        logger.exception('Error occurred while creating activity for '
                         'email-campaign creation. User(id:%s)' % user_id)
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
    schedule_task_params = {"url": EmailCampaignUrl.SEND % email_campaign.id}
    schedule_task_params.update(JSON_CONTENT_TYPE_HEADER)
    if frequency:  # It means its a periodic job, because frequency is 0 in case of one time job.
        schedule_task_params["frequency"] = frequency
        schedule_task_params["task_type"] = SchedulerUtils.PERIODIC  # Change task_type to periodic
        schedule_task_params["start_datetime"] = start_datetime
        schedule_task_params["end_datetime"] = end_datetime
    else:  # It means its a one time Job
        schedule_task_params["task_type"] = SchedulerUtils.ONE_TIME
        schedule_task_params["run_datetime"] = start_datetime if start_datetime else \
            (datetime.datetime.utcnow() +
             datetime.timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S")
    schedule_task_params['is_jwt_request'] = True
    # Schedule email campaign; call Scheduler API
    headers = {'Authorization': oauth_token}
    headers.update(JSON_CONTENT_TYPE_HEADER)
    try:
        scheduler_response = http_request('post', SchedulerApiUrl.TASKS,
                                          headers=headers,
                                          data=json.dumps(schedule_task_params),
                                          user_id=user_id)
    except Exception as ex:
        logger.exception('Exception occurred while calling scheduler. Exception: %s' % ex)
        raise
    if scheduler_response.status_code != 201:
        raise InternalServerError("Error occurred while scheduling email campaign. "
                                  "Status Code: %s, Response: %s"
                                  % (scheduler_response.status_code, scheduler_response.json()))
    scheduler_id = scheduler_response.json()['id']
    # add scheduler task id to email_campaign.
    email_campaign.scheduler_task_id = scheduler_id
    db.session.commit()

    return {'id': email_campaign.id}


def send_emails_to_campaign(campaign, list_ids=None, new_candidates_only=False):
    """
    new_candidates_only sends the emails only to candidates who haven't yet
    received any as part of this campaign.

    :param campaign:    email campaign object
    :param list_ids: list associated with email campaign if given it will take the ids provided else extract out from email campaign object
    :param new_candidates_only: If emails need to be sent to new candidates only i.e. to those candidates whom emails were not sent previously
        If email is sent from client it will not send the actual emails and returns the new html (with url conversions and other replacements)
    :return:            number of emails sent
    """
    if campaign.email_client_id:
        candidate_ids_and_emails = get_email_campaign_candidate_ids_and_emails(campaign=campaign,
                                                                               list_ids=list_ids,
                                                                               new_candidates_only=new_candidates_only)

        # Check if the smart list has more than 0 candidates
        if candidate_ids_and_emails:
            # TODO: IMO (osman also suggested this) Fail Fast
            # TODO:                                 >>> if not:
            # TODO:                                 >>>     raise()
            # TODO:                                 >>> 'rest of the code goes here'
            # TODO: Indentation becomes better
            email_campaign_blast_id, blast_params, blast_datetime = notify_and_get_blast_params(campaign,
                                                                                                new_candidates_only,
                                                                                                candidate_ids_and_emails
                                                                                                )
            list_of_new_email_html_or_text = []
            # Do not send mail if email_client_id is provided
            # Loop through each candidate and get new_html and new_text
            for candidate_id, candidate_address in candidate_ids_and_emails:
                new_text, new_html = get_new_text_html_subject_and_campaign_send(
                    campaign.id, candidate_id, blast_params=blast_params,
                    email_campaign_blast_id=email_campaign_blast_id,
                    blast_datetime=blast_datetime)[:2]
                logger.info("Marketing email added through client %s", campaign.email_client_id)
                resp_dict = dict()
                resp_dict['new_html'] = new_html
                resp_dict['new_text'] = new_text
                resp_dict['email'] = candidate_address
                list_of_new_email_html_or_text.append(resp_dict)
            db.session.commit()

            # TODO: This will be needed later
            # update_candidate_document_on_cloud(user, candidate_ids_and_emails,
            #                                    new_candidates_only, campaign,
            #                                    len(list_of_new_email_html_or_text))
            # Update campaign blast with number of sends
            _update_blast_sends(email_campaign_blast_id, len(candidate_ids_and_emails),
                                campaign, new_candidates_only)
            return list_of_new_email_html_or_text
        else:
            raise InvalidUsage('No candidates with emails found for email_campaign(id:%s).'
                               % campaign.id,
                               error_code=CampaignException.NO_VALID_CANDIDATE_FOUND)
    else:
        # For each candidate, create URL conversions and send the email via Celery task
        send_campaign_through_celery(campaign, list_ids, new_candidates_only)


def send_campaign_to_candidates(candidate_ids_and_emails, blast_params, email_campaign_blast_id,
                                blast_datetime, campaign,
                                new_candidates_only):
    """
    This creates one Celery task per candidate to send campaign emails asynchronously.
    :param candidate_ids_and_emails: list of tuples containing candidate_ids and email addresses
    :param blast_params: email blast params
    :param email_campaign_blast_id: id of email campaign blast object
    :param blast_datetime: email campaign blast datetime
    :param campaign: email campaign object
    :param new_candidates_only: Identifier if candidates are new
    :type candidate_ids_and_emails: list
    :type blast_params: dict
    :type email_campaign_blast_id: int | long
    :type blast_datetime: datetime.datetime
    :type campaign: EmailCampaign
    :type new_candidates_only: bool
    """
    campaign_type = campaign.__tablename__
    callback = post_processing_campaign_sent.subtask((campaign,
                                                      new_candidates_only,
                                                      email_campaign_blast_id,),
                                                     queue=campaign_type)
    # Here we create list of all tasks and assign a self.celery_error_handler() as a
    # callback function in case any of the tasks in the list encounter some error.
    tasks = [send_campaign_to_candidate.subtask(
        (campaign, Candidate.get_by_id(candidate_id), candidate_address,
         blast_params, email_campaign_blast_id, blast_datetime),
        queue=campaign_type) for candidate_id, candidate_address in candidate_ids_and_emails]
    # This runs all tasks asynchronously and sets callback function to be hit once all
    # tasks in list finish running without raising any error. Otherwise callback
    # results in failure status.
    chord(tasks)(callback)


@celery_app.task(name='post_processing_campaign_sent')
def post_processing_campaign_sent(celery_result, campaign,
                                  new_candidates_only,
                                  email_campaign_blast_id):
    logger.info('celery_result: %s' % celery_result)
    sends = celery_result.count(True)
    _update_blast_sends(email_campaign_blast_id, sends, campaign,  new_candidates_only)


@celery_app.task(name='process_campaign_send')
def process_campaign_send(celery_result, campaign, list_ids, new_candidates_only):
    all_candidate_ids = []
    if not celery_result:
        raise InvalidUsage('No candidate(s) found for smartlist_ids %s.' % list_ids,
                           error_code=CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)
    logger.info('celery_result: %s' % celery_result)

    # gather all candidates from various smartlists
    for candidate_list in celery_result:
        all_candidate_ids.extend(list(set(candidate_list)))  # Unique candidates

    subscribed_candidate_ids = handle_subscription(campaign, all_candidate_ids, new_candidates_only)
    candidate_ids_and_emails = get_filtered_email_rows(campaign, subscribed_candidate_ids)
    if candidate_ids_and_emails:
        email_campaign_blast_id, blast_params, blast_datetime = notify_and_get_blast_params(campaign,
                                                                                            new_candidates_only,
                                                                                            candidate_ids_and_emails)
        with app.app_context():
            logger.info('Emails for email campaign (id:%d) are being sent using Celery. Blast ID is %d' %
                        (campaign.id, email_campaign_blast_id))
        send_campaign_to_candidates(candidate_ids_and_emails, blast_params, email_campaign_blast_id,
                                    blast_datetime, campaign,
                                    new_candidates_only)

# This will be used in later version
# def update_candidate_document_on_cloud(user, candidate_ids_and_emails):
#     """
#     Once campaign has been sent to candidates, here we update their documents on cloud search.
#     :param user:
#     :param candidate_ids_and_emails:
#     :return:
#     """
#     try:
#         # Update Candidate Documents in Amazon Cloud Search
#         headers = CampaignBase.get_authorization_header(user.id)
#         headers.update(JSON_CONTENT_TYPE_HEADER)
#         with app.app_context():
#             response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
#                                      data=json.dumps({'candidate_ids': map(itemgetter(0),
#                                                                            candidate_ids_and_emails)}))
#
#         if response.status_code != 204:
#             raise Exception("Status Code: %s Response: %s"
#                             % (response.status_code, response.json()))
#     except Exception as e:
#         error_message = "Couldn't update Candidate Documents in Amazon Cloud Search because: %s" \
#                         % e.message
#         logger.exception(error_message)
#         raise InvalidUsage(error_message)


def get_email_campaign_candidate_ids_and_emails(campaign, list_ids=None, new_candidates_only=False):
    """
    Get candidate ids and email addresses for an email campaign
    :param campaign: Email Campaign Object
    :param list_ids: Ids of smartlists
    :param new_candidates_only: True if campaign is to be sent only to new candidates.
    :return: Returns array of candidate IDs in the campaign's smartlists.
             Is unique.
    """
    if list_ids is None:
        # Get smartlists of this campaign
        list_ids = EmailCampaignSmartlist.get_smartlists_of_campaign(campaign.id,
                                                                     smartlist_ids_only=True)
        if not list_ids:
            raise InvalidUsage('No smartlist is associated with email_campaign(id:%s)' % campaign.id,
                               error_code=CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)

    all_candidate_ids = get_candidates_from_smartlist_for_email_client_id(campaign, list_ids)

    if not all_candidate_ids:
        raise InvalidUsage('No candidate(s) found for smartlist_ids %s.' % list_ids,
                           error_code=CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)
    subscribed_candidate_ids = handle_subscription(campaign, all_candidate_ids, new_candidates_only)
    return get_filtered_email_rows(campaign, subscribed_candidate_ids)


def get_email_campaign_candidate_ids_and_emails_with_celery(campaign, list_ids=None, new_candidates_only=False):
    """
    Get candidates of smartlist through celery task.
    :param campaign: Email Campaign to be sent.
    :param list_ids: Ids of smartlists.
    :param new_candidates_only: True if campaign needs to be sent to new candidates only.
    :return:
    """
    if list_ids is None:
        # Get smartlists of this campaign
        # TODO: Can't we get this from relationship? campaign.smartlists?
        list_ids = EmailCampaignSmartlist.get_smartlists_of_campaign(campaign.id,
                                                                     smartlist_ids_only=True)
    if not list_ids:
        raise InvalidUsage('No smartlist is associated with email_campaign(id:%s)' % campaign.id,
                           error_code=CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
    get_smartlist_candidates_via_celery(campaign, list_ids, new_candidates_only)


def get_candidate_id_email_by_priority(email_info_tuple, email_labels):
    """
    Get the primary_label_id from email_labels tuple list, using that find primary email address in emails_obj.
    If found then simply return candidate_id and primary email_address otherwise return first email address.
    :param (int, str, int) email_info_tuple: (candidate_id, email_address, email_label_id)
    :param [(int, str)] email_labels: Tuple containing structure [( email_label_id, email_label_description )]
    :return: candidate_id, email_address
    :rtype: (int, str)
    """
    if not(isinstance(email_info_tuple, list) and len(email_info_tuple) > 0):
        raise InternalServerError("get_candidate_id_email_by_priority: emails_obj is either not a list or is empty")

    # Get the primary_label_id from email_labels tuple list, using that find primary email address in emails_obj
    # python next method will return the first object from email_labels where primary label matches
    primary_email_id = int(next(email_label_id for email_label_id, email_label_desc in email_labels
                                if email_label_desc.lower() == EmailLabel.PRIMARY_DESCRIPTION.lower()))

    # Find primary email address using email label id
    candidate_email_tuple_iterator = ((candidate_id, email_address) for candidate_id, email_address, email_label_id in email_info_tuple
                                      if email_label_id == primary_email_id)

    candidate_id_and_email_address = next(
        candidate_email_tuple_iterator,
        None)

    # If candidate primary email is found, then just return that
    if candidate_id_and_email_address:
        return candidate_id_and_email_address

    # If primary email not found, then return first email which is last added email
    # Get first tuple from a list of emails_obj and return candidate_id and email_address
    candidate_id, email_address, _ = email_info_tuple[0]
    return candidate_id, email_address


def send_campaign_emails_to_candidate(campaign_id, candidate, candidate_address,
                                      blast_params=None, email_campaign_blast_id=None,
                                      blast_datetime=None):
    """
    This function sends the email to candidate. If working environment is prod, it sends the
    email campaigns to candidates' email addresses, otherwise it sends the email campaign to
    'gettalentmailtest@gmail.com' or email id of user.
    :param campaign_id: email campaign id
    :param candidate: candidate object
    :param candidate_address: candidate email address
    :param blast_params: parameters of email campaign blast
    :param email_campaign_blast_id: id of email campaign blast object
    :param blast_datetime: email campaign blast datetime
    :type campaign_id: int | long
    :type candidate: Candidate
    :type candidate_address: str
    :type blast_params: dict | None
    :type email_campaign_blast_id: int | long | None
    :type blast_datetime: datetime.datetime | None
    """
    campaign = EmailCampaign.get_by_id(campaign_id)
    new_text, new_html, subject, email_campaign_send, blast_params, _ = \
        get_new_text_html_subject_and_campaign_send(campaign.id, candidate.id,
                                                    blast_params=blast_params,
                                                    email_campaign_blast_id=email_campaign_blast_id,
                                                    blast_datetime=blast_datetime)
    logger.info('send_campaign_emails_to_candidate: Candidate id:%s ' % candidate.id)
    # Only in case of production we should send mails to candidate address else mails will
    # go to test account. To avoid spamming actual email addresses, while testing.
    if not CampaignUtils.IS_DEV:
        to_addresses = candidate_address
    else:
        # In dev/staging, only send emails to getTalent users, in case we're
        #  impersonating a customer.
        domain = Domain.get_by_id(campaign.user.domain_id)
        domain_name = domain.name.lower()
        if 'gettalent' in domain_name or 'bluth' in domain_name or 'dice' in domain_name:
            to_addresses = campaign.user.email
        else:
            to_addresses = [app.config[TalentConfigKeys.GT_GMAIL_ID]]
    try:
        email_response = send_email(source='"%s" <no-reply@gettalent.com>' % campaign._from,
                                    # Emails will be sent from <no-reply@gettalent.com> (verified by Amazon SES)
                                    subject=subject,
                                    html_body=new_html or None,
                                    # Can't be '', otherwise, text_body will not show in email
                                    text_body=new_text,
                                    to_addresses=to_addresses,
                                    reply_address=campaign.reply_to.strip(),
                                    # BOTO doesn't seem to work with an array as to_addresses
                                    body=None,
                                    email_format='html' if campaign.body_html else 'text')
    except Exception as e:
        # Mark email as bounced
        _handle_email_sending_error(email_campaign_send, candidate, to_addresses, blast_params,
                                    email_campaign_blast_id, e)
        return False
    # Save SES message ID & request ID
    logger.info("Marketing email sent to %s. Email response=%s", to_addresses, email_response)
    request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
    message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
    email_campaign_send.update(ses_message_id=message_id, ses_request_id=request_id)
    # Add activity
    try:
        CampaignBase.create_activity(campaign.user.id,
                                     Activity.MessageIds.CAMPAIGN_EMAIL_SEND,
                                     email_campaign_send,
                                     dict(campaign_name=campaign.name,
                                          candidate_name=candidate.name))
    except Exception as error:
        logger.exception('Could not add `campaign send activity` for '
                         'email-campaign(id:%s) and User(id:%s) because: '
                         '%s' % (campaign.id, campaign.user.id, error.message))
    return True


@celery_app.task(name='send_campaign_to_candidate')
def send_campaign_to_candidate(campaign, candidate, candidate_address,
                               blast_params, email_campaign_blast_id, blast_datetime):
    """
    For each candidate, this function is called to send email campaign to candidate.
    :param campaign: email campaign object
    :param candidate: candidate object
    :param candidate_address: candidate email address
    :param blast_params: parameters of email campaign blast
    :param email_campaign_blast_id: email campaign blast object id.
    :param blast_datetime: email campaign blast datetime
    :type campaign: EmailCampaign
    :type candidate: Candidate
    :type candidate_address: str
    :type blast_params: dict
    :type email_campaign_blast_id: int|long
    :type blast_datetime: datetime.datetime
    """
    with app.app_context():
        logger.info('sending campaign to candidate(id:%s).' % candidate.id)
        try:
            result_sent = send_campaign_emails_to_candidate(
                campaign_id=campaign.id,
                candidate=candidate,
                # candidates.find(lambda row: row.id == candidate_id).first(),
                candidate_address=candidate_address,
                blast_params=blast_params,
                email_campaign_blast_id=email_campaign_blast_id,
                blast_datetime=blast_datetime
            )
            return result_sent
        except Exception as error:
            logger.exception('Error while sending email campaign(id:%s) to '
                             'candidate(id:%s). Error is: %s'
                             % (campaign.id, candidate.id, error.message))
            db.session.rollback()
            return False


def get_new_text_html_subject_and_campaign_send(campaign_id, candidate_id,
                                                blast_params=None, email_campaign_blast_id=None,
                                                blast_datetime=None):
    """
    This gets new_html and new_text by URL conversion method and returns
    new_html, new_text, subject, email_campaign_send, blast_params, candidate.
    :param campaign_id: Email campaign object id
    :param candidate_id: id of candidate
    :param blast_params: email_campaign blast params
    :param email_campaign_blast_id:  email campaign blast id
    :param blast_datetime: email campaign blast datetime
    :type campaign_id: int | long
    :type candidate_id: int | long
    :type blast_params: dict | None
    :type email_campaign_blast_id: int | long | None
    :type blast_datetime: datetime.datetime | None
    :return:
    """
    # TODO: I think we should solve that detached instance issue more gracefully.
    # TODO: There must be some (you can see sms-svc code. I am passing objects in celery task and it is working fine)
    candidate = Candidate.get_by_id(candidate_id)
    campaign = EmailCampaign.get_by_id(campaign_id)
    # Set the email campaign blast fields if they're not defined, like if this just a test
    if not email_campaign_blast_id:
        email_campaign_blast = EmailCampaignBlast.get_latest_blast_by_campaign_id(campaign.id)
        if not email_campaign_blast:
            logger.error("""send_campaign_emails_to_candidate:
            Must have a previous email_campaign_blast that belongs to this campaign
            if you don't pass in the email_campaign_blast_id param""")
            raise InternalServerError('No email campaign blast found for campaign(id:%s). '
                                      'User(id:%s).' % (campaign.id, campaign.user_id),
                                      error_code=CampaignException.NO_CAMPAIGN_BLAST_FOUND)
        email_campaign_blast_id = email_campaign_blast.id
        blast_datetime = email_campaign_blast.sent_datetime
    if not blast_datetime:
        blast_datetime = datetime.datetime.now()
    if not blast_params:
        email_campaign_blast = EmailCampaignBlast.query.get(email_campaign_blast_id)
        blast_params = dict(sends=email_campaign_blast.sends, bounces=email_campaign_blast.bounces)
    EmailCampaign.session.commit()
    email_campaign_send = EmailCampaignSend(campaign_id=campaign_id,
                                            candidate_id=candidate.id,
                                            sent_datetime=blast_datetime,
                                            blast_id=email_campaign_blast_id)
    EmailCampaignSend.save(email_campaign_send)
    # If the campaign is a subscription campaign, its body & subject are
    # candidate-specific and will be set here
    if campaign.is_subscription:
        pass
    # from TalentJobAlerts import get_email_campaign_fields TODO: Job Alerts?
    #             campaign_fields = get_email_campaign_fields(candidate.id,
    #             do_email_business=do_email_business)
    #             If candidate has no matching job openings, don't send the email
    #             if campaign_fields['total_openings'] < 1:
    #                 return 0
    #             for campaign_field_name, campaign_field_value in campaign_fields.items():
    #                 campaign[campaign_field_name] = campaign_field_value
    new_html, new_text = campaign.body_html or "", campaign.body_text or ""
    logger.info('get_new_text_html_subject_and_campaign_send: candidate_id: %s'
                % candidate.id)

    # Perform MERGETAG replacements
    [new_html, new_text, subject] = do_mergetag_replacements([new_html, new_text,
                                                              campaign.subject], candidate)
    # Perform URL conversions and add in the custom HTML
    logger.info('get_new_text_html_subject_and_campaign_send: email_campaign_send_id: %s'
                % email_campaign_send.id)
    new_text, new_html = \
        create_email_campaign_url_conversions(
            new_html=new_html,
            new_text=new_text,
            is_track_text_clicks=campaign.is_track_text_clicks,
            is_track_html_clicks=campaign.is_track_html_clicks,
            custom_url_params_json=campaign.custom_url_params_json,
            is_email_open_tracking=campaign.is_email_open_tracking,
            custom_html=campaign.custom_html,
            email_campaign_send_id=email_campaign_send.id)
    return new_text, new_html, subject, email_campaign_send, blast_params, candidate


def _handle_email_sending_error(email_campaign_send, candidate, to_addresses, blast_params,
                                email_campaign_blast_id, exception):
    """ If failed to send email; Mark email bounced.
    """
    # If failed to send email, still try to get request id from XML response.
    # Unfortunately XML response is malformed so must manually parse out request id
    request_id_search = re.search('<RequestId>(.*)</RequestId>', exception.__str__(), re.IGNORECASE)
    request_id = request_id_search.group(1) if request_id_search else None
    email_campaign_send.ses_request_id = request_id
    db.session.commit()
    # Send failure message to email marketing admin, just to notify for verification
    logger.exception("Failed to send marketing email to candidate_id=%s, to_addresses=%s"
                     % (candidate.id, to_addresses))


def update_hit_count(url_conversion):
    try:
        # Increment hit count for email marketing
        new_hit_count = (url_conversion.hit_count or 0) + 1
        url_conversion.hit_count = new_hit_count
        url_conversion.last_hit_time = datetime.datetime.now()
        db.session.commit()
        email_campaign_send_url_conversion = EmailCampaignSendUrlConversion.query.filter_by(
            url_conversion_id=url_conversion.id).first()
        email_campaign_send = email_campaign_send_url_conversion.email_campaign_send
        candidate = Candidate.query.get(email_campaign_send.candidate_id)
        is_open = email_campaign_send_url_conversion.type == TRACKING_URL_TYPE
        # If candidate has been deleted, don't make the activity
        if not candidate or candidate.is_web_hidden:
            logger.info("Tried performing URL redirect for nonexistent candidate: %s. "
                        "email_campaign_send: %s",
                        email_campaign_send.candidate_id, email_campaign_send.id)
        else:
            # Add activity
            try:
                CampaignBase.create_activity(candidate.user_id,
                                             Activity.MessageIds.CAMPAIGN_EMAIL_OPEN if is_open
                                             else Activity.MessageIds.CAMPAIGN_EMAIL_CLICK,
                                             email_campaign_send,
                                             dict(candidateId=candidate.id,
                                                  campaign_name=email_campaign_send.email_campaign.name,
                                                  candidate_name=candidate.formatted_name))
            except Exception as error:
                logger.error('Error occurred while creating activity for '
                             'email-campaign(id:%s) open/click. '
                             'Error is %s' % (email_campaign_send.campaign_id,
                                              error.message))
            logger.info("Activity has been added for URL redirect for candidate(id:%s). "
                        "email_campaign_send(id:%s)",
                        email_campaign_send.candidate_id, email_campaign_send.id)

        # Update email_campaign_blast entry only if it's a new hit
        if new_hit_count == 1:
            email_campaign_blast = EmailCampaignBlast.query.filter_by(
                sent_datetime=email_campaign_send.sent_datetime,
                campaign_id=email_campaign_send.campaign_id).first()
            if email_campaign_blast:
                if is_open:
                    email_campaign_blast.opens += 1
                else:
                    email_campaign_blast.html_clicks += 1
                db.session.commit()
            else:
                logger.error("Email campaign URL redirect: No email_campaign_blast found matching "
                             "email_campaign_send.sent_datetime %s, campaign_id=%s"
                             % (email_campaign_send.sent_datetime,
                                email_campaign_send.campaign_id))
    except Exception:
        logger.exception("Received exception doing url_redirect (url_conversion_id=%s)",
                         url_conversion.id)


def get_subscription_preference(candidate_id):
    """
    If there are multiple subscription preferences (due to legacy reasons),
    if any one is 1-6, keep it and delete the rest.
    Otherwise, if any one is NULL, keep it and delete the rest.
    Otherwise, if any one is 7, delete all of them.
    """
    # Not used but keeping it because same function was somewhere else in other service but using hardcoded ids.
    # So this one can be used to replace the old function.
    email_prefs = db.session.query(CandidateSubscriptionPreference).filter_by(
        candidate_id=candidate_id)
    non_custom_frequencies = db.session.query(Frequency.id).filter(
        Frequency.name.in_(Frequency.standard_frequencies().keys())).all()
    non_custom_frequency_ids = [non_custom_frequency[0] for non_custom_frequency in
                                non_custom_frequencies]
    non_custom_pref = email_prefs.filter(
        CandidateSubscriptionPreference.frequency_id.in_(
            non_custom_frequency_ids)).first()  # Other freqs.
    null_pref = email_prefs.filter(CandidateSubscriptionPreference.frequency_id == None).first()
    custom_frequency = Frequency.get_seconds_from_id(Frequency.CUSTOM)
    custom_pref = email_prefs.filter(
        CandidateSubscriptionPreference.frequency_id == custom_frequency.id).first()  # Custom freq.
    if non_custom_pref:
        all_other_prefs = email_prefs.filter(
            CandidateSubscriptionPreference.id != non_custom_pref.id)
        all_other_prefs_ids = [row.id for row in all_other_prefs]
        logger.info("get_subscription_preference: Deleting non-custom prefs for candidate %s: %s",
                    candidate_id, all_other_prefs_ids)
        db.session.query(CandidateSubscriptionPreference) \
            .filter(CandidateSubscriptionPreference.id.in_(all_other_prefs_ids)).delete(
            synchronize_session='fetch')
        return non_custom_pref
    elif null_pref:
        non_null_prefs = email_prefs.filter(CandidateSubscriptionPreference.id != null_pref.id)
        non_null_prefs_ids = [row.id for row in non_null_prefs]
        logger.info("get_subscription_preference: Deleting non-null prefs for candidate %s: %s",
                    candidate_id, non_null_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
            CandidateSubscriptionPreference.id.in_(non_null_prefs_ids)).delete(
            synchronize_session='fetch')
        return null_pref
    elif custom_pref:
        email_prefs_ids = [row.id for row in email_prefs]
        logger.info("get_subscription_preference: Deleting all prefs for candidate %s: %s",
                    candidate_id,
                    email_prefs_ids)
        db.session.query(CandidateSubscriptionPreference).filter(
            CandidateSubscriptionPreference.id.in_(email_prefs_ids)).delete(
            synchronize_session='fetch')
        return None


def _update_blast_sends(blast_id, new_sends, campaign, new_candidates_only):
    """
    This updates the email campaign blast object with number of sends and logs that
    Marketing email batch completed.
    :param blast_id: Id of blast object.
    :param new_sends: Number of new sends.
    :param campaign: EMail Campaign.
    :param new_candidates_only: True if campaign is to be sent to new candidates only.
    """
    blast_obj = EmailCampaignBlast.get_by_id(blast_id)
    blast_obj.update(sends=blast_obj.sends + new_sends)
    # This will be needed later
    # update_candidate_document_on_cloud(user, candidate_ids_and_emails)
    logger.info("Marketing email batch completed, emails sent=%s, "
                "campaign=%s, user=%s, new_candidates_only=%s",
                new_sends, campaign.name, campaign.user.email, new_candidates_only)


def handle_email_bounce(message_id, bounce, emails):
    """
    This function handles email bounces. When an email is bounced, email address is marked as bounced so
    no further emails will be sent to this email address.
    It also updates email campaign bounces in respective blast.
    :param str message_id: message id associated with email send
    :param dict bounce: JSON bounce message body
    :param list[str] emails: list of bounced emails
    """
    assert isinstance(message_id, basestring) and message_id, "message_id should not be empty"
    assert isinstance(bounce, dict) and bounce, "bounce param should be a valid dict"
    assert isinstance(emails, list) and all(emails), "emails param should be a non empty list of email addresses"
    logger.info('Bounce Detected: %s', bounce)

    # get the corresponding EmailCampaignSend object that is associated with given AWS message id
    send_obj = EmailCampaignSend.get_by_amazon_ses_message_id(message_id)

    if not send_obj:
        logger.error('Unable to find email campaign send for this email bounce: %s', bounce)
        return None

    # Mark the send object as bounced.
    send_obj.update(is_ses_bounce=True)
    blast = send_obj.blast

    # increase number of bounces by one for associated campaign blast.
    blast.update(bounces=(blast.bounces + 1))

    """
    There are two types of Bounces:
        1. Permanent Bounces: Bounces that are caused by invalid email address or an email that is
        in suppressed list.
        2. Temporary Bounces: Bounces that can be retried, caused by:
            - MailboxFull
            - MessageTooLarge
            - ContentRejected
            - AttachmentRejected
    """
    if bounce['bounceType'] == AWS_SNS_TERMS.PERMANENT_BOUNCE:
        # Mark the matching emails as bounced in all domains because an email that is invalid
        # would be invalid in all domains.
        CandidateEmail.mark_emails_bounced(emails)
        logger.info('Marked %s email addresses as bounced' % emails)
    elif bounce['bounceType'] == AWS_SNS_TERMS.TEMPORARY_BOUNCE:
        logger.info('Email was bounced as Transient. '
                    'We will not mark it bounced because it is a temporary problem')


def get_candidates_from_smartlist_for_email_client_id(campaign, list_ids):
    all_candidate_ids = []
    for list_id in list_ids:
        # Get candidates present in smartlist
        try:
            smartlist_candidate_ids = get_candidates_of_smartlist(list_id, candidate_ids_only=True)
            # gather all candidates from various smartlists
            all_candidate_ids.extend(smartlist_candidate_ids)
        except Exception as error:
            logger.exception('Error occurred while getting candidates of smartlist(id:%s).'
                             'EmailCampaign(id:%s) User(id:%s). Reason: %s'
                             % (list_id, campaign.id, campaign.user.id, error.message))
    all_candidate_ids = list(set(all_candidate_ids))  # Unique candidates
    return all_candidate_ids


def handle_subscription(campaign, all_candidate_ids, new_candidates_only):
    """
    Takes campaign and all candidate ids as arguments and process them to return
    the ids of subscribed candidates.
    :param campaign: email campaign
    :param all_candidate_ids: ids of all candidates to whome we are going to send campaign
    :param new_candidates_only: if campaign is to be sent only to new candidates
    :return: ids of subscribed candidates
    """
    if campaign.is_subscription:
        # If the campaign is a subscription campaign,
        # only get candidates subscribed to the campaign's frequency
        subscribed_candidates_rows = CandidateSubscriptionPreference.with_entities(
            CandidateSubscriptionPreference.candidate_id).filter(
            and_(CandidateSubscriptionPreference.candidate_id.in_(all_candidate_ids),
                 CandidateSubscriptionPreference.frequency_id == campaign.frequency_id)).all()
        subscribed_candidate_ids = [row.candidate_id for row in
                                    subscribed_candidates_rows]  # Subscribed candidate ids
        if not subscribed_candidate_ids:
            logger.error("No candidates in subscription campaign %s", campaign)

    else:
        # Otherwise, just filter out unsubscribed candidates:
        # their subscription preference's frequencyId is NULL, which means 'Never'
        unsubscribed_candidate_ids = []
        for candidate_id in all_candidate_ids:
            # Call candidate API to get candidate's subscription preference.
            subscription_preference = get_candidate_subscription_preference(candidate_id, campaign.user.id)
            # campaign_subscription_preference = get_subscription_preference(candidate_id)
            logger.debug("subscription_preference: %s" % subscription_preference)
            if subscription_preference and not subscription_preference.get('frequency_id'):
                unsubscribed_candidate_ids.append(candidate_id)

        # Remove un-subscribed candidates
        subscribed_candidate_ids = list(set(all_candidate_ids) - set(unsubscribed_candidate_ids))

    # If only getting candidates that haven't been emailed before...
    if new_candidates_only:
        already_emailed_candidates = EmailCampaignSend.query.with_entities(
            EmailCampaignSend.candidate_id).filter_by(campaign_id=campaign.id).all()
        emailed_candidate_ids = [row.candidate_id for row in already_emailed_candidates]

        # Filter out already emailed candidates from subscribed_candidate_ids, so we have new candidate_ids only
        new_candidate_ids = list(set(subscribed_candidate_ids) - set(emailed_candidate_ids))
        # assign it to subscribed_candidate_ids (doing it explicit just to make it clear)
        subscribed_candidate_ids = new_candidate_ids
    return subscribed_candidate_ids


def get_smartlist_candidates_via_celery(campaign, list_ids, new_candidates_only):
    """
    Get candidates of given smartlist by creating celery task for each smartlist.
    :param campaign: Email Campiagn
    :param list_ids: Ids of smartlists
    :param new_candidates_only: True if only new candidates are to be returned.
    :return:
    """
    campaign_type = campaign.__tablename__
    callback = process_campaign_send.subtask((campaign, list_ids, new_candidates_only, ),
                                             queue=campaign_type)

    # Get candidates present in smartlist
    # Here we create list of all tasks and assign a self.celery_error_handler() as a
    # callback function in case any of the tasks in the list encounter some error.
    tasks = [get_candidates_from_smartlist.subtask(
        (list_id, campaign, True, campaign.user.id),
        queue=campaign_type) for list_id in list_ids]
    # This runs all tasks asynchronously and sets callback function to be hit once all
    # tasks in list finish running without raising any error. Otherwise callback
    # results in failure status.
    result = chord(tasks)(callback)


def get_filtered_email_rows(campaign, subscribed_candidate_ids):
    """
    Filter email addresses of candidates to eliminate duplicates and/or multiple addresses for
    any candidate.
    :param campaign: Email Campaign
    :param subscribed_candidate_ids: Ids of subscribed candidates.
    :return:
    """
    # Get candidate emails sorted by updated time and then by candidate_id
    candidate_email_rows = CandidateEmail.query.with_entities(CandidateEmail.candidate_id,
                                                              CandidateEmail.address,
                                                              CandidateEmail.updated_time,
                                                              CandidateEmail.email_label_id) \
        .filter(CandidateEmail.candidate_id.in_(subscribed_candidate_ids)) \
        .order_by(desc(CandidateEmail.updated_time), CandidateEmail.candidate_id)
    """
        candidate_email_rows data will be
        1   candidate0_ryk@gmail.com    2016-02-20T11:22:00Z    1
        1   candidate0_lhr@gmail.com    2016-03-20T11:22:00Z    2
        2   candidate1_isb@gmail.com    2016-02-20T11:22:00Z    4
        2   candidate1_lhr@gmail.com    2016-03-20T11:22:00Z    3
    """

    # list of tuples (candidate id, email address)
    group_id_and_email_and_labels = []

    # ids_and_email_and_labels will be [(1, 'saad_ryk@hotmail.com', 1), (2, 'saad_lhr@gmail.com', 3), ...]
    # id_email_label: (id, email, label)
    ids_and_email_and_labels = [(row.candidate_id, row.address, row.email_label_id) for row in candidate_email_rows]

    """
    After running groupby clause, the data will look like
    group_id_and_email_and_labels = [[(candidate_id1, email_address1, email_label1),
        (candidate_id2, email_address2, email_label2)],... ]
    """

    for key, group_id_email_label in itertools.groupby(ids_and_email_and_labels, lambda id_email_label: id_email_label[0]):
        group_id_and_email_and_labels.append(list(group_id_email_label))
    filtered_email_rows = []

    # Check if primary EmailLabel exist in db
    if not EmailLabel.get_primary_label_description() == EmailLabel.PRIMARY_DESCRIPTION:
        raise InternalServerError(
            "get_email_campaign_candidate_ids_and_emails: Email label with primary description not found in db.")

    # We don't know email_label id of primary email. So, get that from db
    email_label_id_desc_tuples = [(email_label.id, email_label.description) for email_label in EmailLabel.query.all()]

    # If there are multiple emails of a single candidate, then get the primary email if it exist, otherwise get any
    # other email
    for id_and_email_and_label in group_id_and_email_and_labels:
        _id, email = get_candidate_id_email_by_priority(id_and_email_and_label, email_label_id_desc_tuples)
        search_result = CandidateEmail.search_email_in_user_domain(User, campaign.user, email)
        # If there is only one candidate for an email-address in user's domain, we are good to go,
        # otherwise log and raise the invalid error.
        if len(search_result) == 1:
            if CandidateEmail.is_bounced_email(email):
                logger.info('Skipping this email because this email address is marked as bounced.'
                            'CandidateId : %s, Email: %s, EmailCampaignId: %s' % (_id, email, campaign.id))
                continue
            filtered_email_rows.append((_id, email))
        else:
            logger.warn('%s candidates found for email address %s in user(id:%s)`s domain(id:%s). '
                        'Candidate ids are: %s'
                        % (len(search_result), email, campaign.user.id, campaign.user.domain_id,
                           [candidate_email.candidate_id for candidate_email in search_result]))
            raise InvalidUsage('There exist multiple candidates with same email address '
                               'in user`s domain')
    return filtered_email_rows


def notify_and_get_blast_params(campaign, new_candidates_only, candidate_ids_and_emails):
    """
    Notifies admins that email campaign is about to be sent shortly. Also returns blast params
    for the intended campaign.
    :param campaign: Email Campaign
    :param new_candidates_only: True if campaign needs to be sent to new candidates only.
    :param candidate_ids_and_emails: Ids and email addresses of candidates.
    :return:
    """
    with app.app_context():
        email_notification_to_admins(
            subject='Marketing batch about to send',
            body="Marketing email batch about to send, campaign.name=%s, user=%s, "
                 "new_candidates_only=%s, address list size=%s"
                 % (campaign.name, campaign.user.email, new_candidates_only, len(candidate_ids_and_emails))
                )
        logger.info("Marketing email batch about to send, campaign.name=%s, user=%s, "
                    "new_candidates_only=%s, address list size=%s"
                    % (campaign.name, campaign.user.email, new_candidates_only,
                        len(candidate_ids_and_emails)))
    # Add activity
    try:
        CampaignBase.create_activity(campaign.user.id,
                                     Activity.MessageIds.CAMPAIGN_SEND,
                                     campaign,
                                     dict(id=campaign.id, name=campaign.name,
                                          num_candidates=len(candidate_ids_and_emails)))
    except Exception as error:
        with app.app_context():
            logger.error('Error occurred while creating activity for '
                         'email-campaign(id:%s) batch send. Error is %s'
                         % (campaign.id, error.message))
    # Create the email_campaign_blast for this blast
    blast_datetime = datetime.datetime.now()
    email_campaign_blast = EmailCampaignBlast(campaign_id=campaign.id,
                                              sent_datetime=blast_datetime)
    EmailCampaignBlast.save(email_campaign_blast)
    blast_params = dict(sends=0, bounces=0)
    return email_campaign_blast.id, blast_params, blast_datetime


def send_campaign_through_celery(campaign, list_ids, new_candidates_only):
    """
    Sends email campaign using celery workers.
    :param campaign: Email Campaign to be sent.
    :param list_ids: Ids of smartlists.
    :param new_candidates_only: True if email campaign needs to be sent to new candidates only.
    """
    get_email_campaign_candidate_ids_and_emails_with_celery(campaign, list_ids, new_candidates_only)
