"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Um-I-Hani, QC-Technologies, <haniqadri.qc@gmail.com>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains function used by email-campaign-api.
"""
# Standard Imports
import re
import json
import getpass
from datetime import datetime, timedelta

# Third Party
from celery import chord
from redo import retrier
from requests import codes

# Service Specific
from email_campaign_service.modules.email_clients import SMTP
from email_campaign_service.modules import aws_constants as aws
from email_campaign_service.json_schema.test_email import TEST_EMAIL_SCHEMA
from email_campaign_service.modules.validations import get_or_set_valid_value
from email_campaign_service.email_campaign_app import (logger, celery_app, app)
from email_campaign_service.modules.utils import (TRACKING_URL_TYPE, get_candidates_from_smartlist,
                                                  do_mergetag_replacements, create_email_campaign_url_conversions,
                                                  decrypt_password, get_priority_emails)

# Common Utils
from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.user import Domain
from email_campaign_service.common.models.misc import (Frequency, Activity)
from email_campaign_service.common.utils.scheduler_utils import SchedulerUtils
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.routes import SchedulerApiUrl, EmailCampaignApiUrl
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.campaign_services.custom_errors import CampaignException
from email_campaign_service.common.models.email_campaign import (EmailCampaign,
                                                                 EmailCampaignSmartlist,
                                                                 EmailCampaignBlast,
                                                                 EmailCampaignSend,
                                                                 EmailCampaignSendUrlConversion)
from email_campaign_service.common.models.candidate import (Candidate, CandidateEmail,
                                                            CandidateSubscriptionPreference)
from email_campaign_service.common.error_handling import (InvalidUsage, InternalServerError)
from email_campaign_service.common.utils.talent_reporting import email_notification_to_admins
from email_campaign_service.common.campaign_services.validators import validate_smartlist_ids
from email_campaign_service.common.utils.amazon_ses import (send_email, get_default_email_info)
from email_campaign_service.common.utils.handy_functions import (http_request, JSON_CONTENT_TYPE_HEADER)
from email_campaign_service.common.utils.validators import (raise_if_not_instance_of, get_json_data_if_validated,
                                                            raise_if_not_positive_int_or_long)
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import get_candidates_of_smartlist
from email_campaign_service.common.inter_service_calls.candidate_service_calls import \
    get_candidate_subscription_preference


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


def create_email_campaign(user_id, oauth_token, name, subject, description, _from, reply_to, body_html,
                          body_text, list_ids, email_client_id=None, frequency_id=None,
                          email_client_credentials_id=None, base_campaign_id=None, start_datetime=None,
                          end_datetime=None, template_id=None):
    """
    Creates a new email campaign.
    Schedules email campaign.

    :return: newly created email_campaign's id
    """
    frequency = Frequency.get_seconds_from_id(frequency_id)
    email_campaign = EmailCampaign(name=name, user_id=user_id, is_hidden=0, subject=subject,
                                   description=description,
                                   _from=get_or_set_valid_value(_from, basestring, '').strip(),
                                   reply_to=get_or_set_valid_value(reply_to, basestring, '').strip(),
                                   body_html=body_html, body_text=body_text, start_datetime=start_datetime,
                                   end_datetime=end_datetime, frequency_id=frequency_id if frequency_id else None,
                                   email_client_id=email_client_id,
                                   email_client_credentials_id=email_client_credentials_id
                                   if email_client_credentials_id else None,
                                   base_campaign_id=base_campaign_id if base_campaign_id else None
                                   )
    EmailCampaign.save(email_campaign)

    # Create activity in a celery task
    celery_create_activity.delay(user_id, Activity.MessageIds.CAMPAIGN_CREATE, email_campaign,
                                 dict(id=email_campaign.id, name=name),
                                 'Error occurred while creating activity for email-campaign creation. User(id:%s)'
                                 % user_id)

    # create email_campaign_smartlist record
    create_email_campaign_smartlists(smartlist_ids=list_ids, email_campaign_id=email_campaign.id)

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

    headers = {'Authorization': oauth_token}
    headers.update(JSON_CONTENT_TYPE_HEADER)
    send_url = EmailCampaignApiUrl.SEND % email_campaign.id

    if not start_datetime:  # Send campaign immediately
        send_response = http_request('post', send_url, headers=headers, user_id=user_id)
        if send_response.status_code != codes.OK:
            raise InternalServerError("Error occurred while sending email-campaign. Status Code: %s, Response: %s"
                                      % (send_response.status_code, send_response.json()))
        logger.info('Email campaign(id:%s) is being sent immediately.' % email_campaign.id)
    else:  # Schedule the sending of emails & update email_campaign scheduler fields
        schedule_task_params = {"url": send_url}
        schedule_task_params.update(JSON_CONTENT_TYPE_HEADER)
        if frequency:  # It means its a periodic job, because frequency is 0 in case of one time job.
            schedule_task_params["frequency"] = frequency
            schedule_task_params["task_type"] = SchedulerUtils.PERIODIC  # Change task_type to periodic
            schedule_task_params["start_datetime"] = start_datetime
            schedule_task_params["end_datetime"] = end_datetime
        else:  # It means its a one time Job
            schedule_task_params["task_type"] = SchedulerUtils.ONE_TIME
            schedule_task_params["run_datetime"] = start_datetime
        schedule_task_params['is_jwt_request'] = True
        # Schedule email campaign; call Scheduler API
        try:
            scheduler_response = http_request('post', SchedulerApiUrl.TASKS, headers=headers,
                                              data=json.dumps(schedule_task_params), user_id=user_id)
        except Exception as ex:
            logger.exception('Exception occurred while calling scheduler. Exception: %s' % ex)
            raise
        if scheduler_response.status_code != codes.CREATED:
            raise InternalServerError("Error occurred while scheduling email campaign. "
                                      "Status Code: %s, Response: %s"
                                      % (scheduler_response.status_code, scheduler_response.json()))
        scheduler_id = scheduler_response.json()['id']
        # add scheduler task id to email_campaign.
        email_campaign.scheduler_task_id = scheduler_id

    db.session.commit()
    return {'id': email_campaign.id}


def send_email_campaign(current_user, campaign, new_candidates_only=False):
    """
    This function handles the actual sending of email campaign to candidates.
    Emails are sent to new candidates only if new_candidates_only is true. In case campaign has
    email_client_id associated with it (in case request came from browser plugins), we don't send
    actual emails and just send the required fields (new_html, new_text etc) back in response.
    Otherwise we get candidates from smartlists through celery and also send emails to those
    candidates via celery.
    :param current_user: User object
    :param campaign: Valid EmailCampaign object.
    :param new_candidates_only: True if email needs to be sent to those candidates whom emails were not sent previously
    :type user_id: int | long
    :type campaign: EmailCampaign
    :type new_candidates_only: bool
    """
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError(error_message='Must provide valid EmailCampaign object.')
    raise_if_not_instance_of(new_candidates_only, bool)
    campaign_id = campaign.id

    # Get smartlists of this campaign
    smartlist_ids = EmailCampaignSmartlist.get_smartlists_of_campaign(campaign_id, smartlist_ids_only=True)
    if not smartlist_ids:
        raise InvalidUsage('No smartlist is associated with email_campaign(id:%s)' % campaign.id,
                           error_code=CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
    # Validation for list ids belonging to same domain
    validate_smartlist_ids(smartlist_ids, current_user)

    if campaign.email_client_id:  # gt plugin code starts here.
        candidate_ids_and_emails, unsubscribed_candidates = get_email_campaign_candidate_ids_and_emails(campaign,
                                                                                                        smartlist_ids,
                                                                                                        new_candidates_only=new_candidates_only)

        # Check if the smartlist has more than 0 candidates
        if not candidate_ids_and_emails:
            raise InvalidUsage('No candidates with emails found for email_campaign(id:%s).' % campaign.id,
                               error_code=CampaignException.NO_VALID_CANDIDATE_FOUND)
        else:
            email_campaign_blast_id, blast_params, blast_datetime = \
                notify_and_get_blast_params(campaign, new_candidates_only, candidate_ids_and_emails)
            _update_blast_unsubscribed_candidates(email_campaign_blast_id, len(unsubscribed_candidates))
            list_of_new_email_html_or_text = []
            # Do not send mail if email_client_id is provided
            # Loop through each candidate and get new_html and new_text
            for candidate_id, candidate_address in candidate_ids_and_emails:
                new_text, new_html = get_new_text_html_subject_and_campaign_send(
                    campaign.id, candidate_id, candidate_address, blast_params=blast_params,
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
    # For each candidate, create URL conversions and send the email via Celery task
    get_smartlist_candidates_via_celery(current_user.id, campaign_id, smartlist_ids, new_candidates_only)


def send_campaign_to_candidates(user_id, candidate_ids_and_emails, blast_params, email_campaign_blast_id,
                                blast_datetime, campaign,
                                new_candidates_only):
    """
    This creates one Celery task per candidate to send campaign emails asynchronously.
    :param user_id: ID of user
    :param candidate_ids_and_emails: list of tuples containing candidate_ids and email addresses
    :param blast_params: email blast params
    :param email_campaign_blast_id: id of email campaign blast object
    :param blast_datetime: email campaign blast datetime
    :param campaign: EmailCampaign object
    :param new_candidates_only: Identifier if candidates are new
    :type user_id: int | long
    :type candidate_ids_and_emails: list
    :type blast_params: dict
    :type email_campaign_blast_id: int | long
    :type blast_datetime: datetime.datetime
    :type campaign: EmailCampaign
    :type new_candidates_only: bool
    """
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError(error_message='Must provide valid EmailCampaign object.')
    if not candidate_ids_and_emails:
        raise InternalServerError(error_message='No candidate data provided.')
    if not blast_params:
        raise InternalServerError(error_message='Blast Params must be provided.')
    if not email_campaign_blast_id:
        raise InternalServerError(error_message='email_campaign_blast_id must be provided.')
    campaign_type = campaign.__tablename__
    callback = post_processing_campaign_sent.subtask((campaign, new_candidates_only, email_campaign_blast_id,),
                                                     queue=campaign_type)

    # Here we create list of all tasks.
    tasks = [send_email_campaign_to_candidate.subtask((user_id, campaign, candidate_id, candidate_address,
             blast_params, email_campaign_blast_id, blast_datetime), link_error=celery_error_handler(
             campaign_type), queue=campaign_type) for candidate_id, candidate_address in candidate_ids_and_emails]
    # This runs all tasks asynchronously and sets callback function to be hit once all
    # tasks in list finish running without raising any error. Otherwise callback
    # results in failure status.
    chord(tasks)(callback)


@celery_app.task(name='post_processing_campaign_sent')
def post_processing_campaign_sent(celery_result, campaign, new_candidates_only, email_campaign_blast_id):
    """
    Callback for all celery tasks sending campaign emails to candidates. celery_result would contain the return
    values of all the tasks, we would update the sends count with the number of email sending tasks that were
    successful.
    :param celery_result: result af all celery tasks
    :param campaign: Valid EmailCampaign object
    :param new_candidates_only: True if emails sent to new candidates only
    :param email_campaign_blast_id: Id of blast object for specified campaign
    :type celery_result: list
    :type campaign: EmailCampaign
    :type new_candidates_only: bool
    :type email_campaign_blast_id: int | long
    """
    with app.app_context():
        if not celery_result:
            logger.error('Celery task sending campaign(id;%s) emails failed' % campaign.id)
            return
        if not isinstance(campaign, EmailCampaign):
            logger.error('Campaign object is not valid')
            return
        if not isinstance(new_candidates_only, bool):
            logger.error('new_candidates_only must be bool')
            return
        if not isinstance(email_campaign_blast_id, (int, long)) or email_campaign_blast_id <= 0:
            logger.error('email_campaign_blast_id must be positive int or long')
            return
        logger.info('celery_result: %s' % celery_result)
    sends = celery_result.count(True)
    _update_blast_sends(email_campaign_blast_id, sends, campaign,  new_candidates_only)


@celery_app.task(name='process_campaign_send')
def process_campaign_send(celery_result, user_id, campaign_id, list_ids, new_candidates_only=False):
    """
     Callback after getting candidate data of all smartlists. Results from all the smartlists
     are present in celery_result and we use that for further processing of the campaign. That includes
     filtering the results sending actual campaign emails.
     :param celery_result: Combined result of all celery tasks.
     :param user_id: Id of user.
     :param campaign_id: Campaign Id.
     :param list_ids: Ids of all smartlists associated with the campaigns.
     :param new_candidates_only: True if only new candidates need to be fetched.
     :type celery_result: list
     :type user_id: int | long
     :type campaign_id: int | long
     :type list_ids: list
     :type new_candidates_only: bool
    """
    all_candidate_ids = []
    with app.app_context():
        if not celery_result:
            logger.error('No candidate(s) found for smartlist_ids %s, campaign_id: %s'
                         'user_id: %s.' % list_ids, campaign_id, user_id)
            return
        if not isinstance(user_id, (int, long)) or user_id <= 0:
            logger.error('user_id must be positive int of long')
        if not isinstance(campaign_id, (int, long)) or campaign_id <= 0:
            logger.error('campaign_id must be positive int of long')
            return
        if not isinstance(list_ids, list) or len(list_ids) < 0:
            logger.error('list_ids are mandatory')
            return
        if not isinstance(new_candidates_only, bool):
            logger.error('new_candidates_only must be bool')
            return
        logger.info('celery_result: %s' % celery_result)

    # gather all candidates from various smartlists
    for candidate_list in celery_result:
        all_candidate_ids.extend(candidate_list)
    all_candidate_ids = list(set(all_candidate_ids))  # Unique candidates
    campaign = EmailCampaign.get_by_id(campaign_id)
    subscribed_candidate_ids, unsubscribed_candidates_ids = get_subscribed_and_unsubscribed_candidates_ids(campaign,
                                                                                                           all_candidate_ids,
                                                                                                           new_candidates_only)
    candidate_ids_and_emails = get_priority_emails(campaign.user, subscribed_candidate_ids)
    if candidate_ids_and_emails:
        email_campaign_blast_id, blast_params, blast_datetime = notify_and_get_blast_params(campaign,
                                                                                            new_candidates_only,
                                                                                            candidate_ids_and_emails)
        _update_blast_unsubscribed_candidates(email_campaign_blast_id, len(unsubscribed_candidates_ids))
        with app.app_context():
            logger.info('Emails for email campaign (id:%d) are being sent using Celery. Blast ID is %d' %
                        (campaign.id, email_campaign_blast_id))
        send_campaign_to_candidates(user_id, candidate_ids_and_emails, blast_params, email_campaign_blast_id,
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


def get_email_campaign_candidate_ids_and_emails(campaign, smartlist_ids, new_candidates_only=False):
    """
    Get candidate ids and email addresses for an email campaign
    :param campaign: EmailCampaign object
    :param smartlist_ids: List of ids of smartlists associated with given campaign
    :param new_candidates_only: True if campaign is to be sent only to new candidates.
    :type campaign: EmailCampaign
    :type smartlist_ids: list
    :type new_candidates_only: bool
    :return: Returns dict of unique candidate IDs in the campaign's smartlists.
    :rtype list
    """
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError(error_message='Must provide valid EmailCampaign object.')
    raise_if_not_instance_of(new_candidates_only, bool)
    all_candidate_ids = get_candidates_from_smartlist_for_email_client_id(campaign, smartlist_ids)
    if not all_candidate_ids:
        raise InternalServerError('No candidate(s) found for smartlist_ids %s.' % smartlist_ids,
                                  error_code=CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)
    subscribed_candidate_ids, unsubscribed_candidates_ids = get_subscribed_and_unsubscribed_candidates_ids(campaign, all_candidate_ids, new_candidates_only)
    return get_priority_emails(campaign.user, subscribed_candidate_ids), unsubscribed_candidates_ids


def send_campaign_emails_to_candidate(user_id, campaign_id, candidate_id, candidate_address, blast_params=None,
                                      email_campaign_blast_id=None, blast_datetime=None):
    """
    This function sends the email to candidate. If working environment is prod, it sends the
    email campaigns to candidates' email addresses, otherwise it sends the email campaign to
    'gettalentmailtest@gmail.com' or email id of user.
    :param user_id: user object
    :param campaign_id: email campaign id
    :param candidate_id: candidate id
    :param candidate_address: candidate email address
    :param blast_params: parameters of email campaign blast
    :param email_campaign_blast_id: id of email campaign blast object
    :param blast_datetime: email campaign blast datetime
    :type user_id: int | long
    :type campaign_id: int | long
    :type candidate_id: int | long
    :type candidate_address: str
    :type blast_params: dict | None
    :type email_campaign_blast_id: int | long | None
    :type blast_datetime: datetime | None
    """
    raise_if_not_positive_int_or_long(user_id)
    raise_if_not_positive_int_or_long(campaign_id)
    raise_if_not_positive_int_or_long(candidate_id)

    if email_campaign_blast_id:
        raise_if_not_positive_int_or_long(email_campaign_blast_id)

    raise_if_not_instance_of(candidate_address, basestring)

    if blast_datetime:
        raise_if_not_instance_of(blast_datetime, datetime)

    if blast_params:
        raise_if_not_instance_of(blast_params, dict)

    campaign = EmailCampaign.get_by_id(campaign_id)
    candidate = Candidate.get_by_id(candidate_id)
    new_text, new_html, subject, email_campaign_send, blast_params, _ = \
        get_new_text_html_subject_and_campaign_send(campaign.id, candidate_id, candidate_address,
                                                    blast_params=blast_params,
                                                    email_campaign_blast_id=email_campaign_blast_id,
                                                    blast_datetime=blast_datetime)
    logger.info('send_campaign_emails_to_candidate: Candidate id:%s ' % candidate_id)
    # Only in case of production we should send mails to candidate address else mails will
    # go to test account. To avoid spamming actual email addresses, while testing.
    if not CampaignUtils.IS_DEV:
        to_address = candidate_address
    else:
        # In dev/staging, only send emails to getTalent users, in case we're
        #  impersonating a customer.
        domain = Domain.get_by_id(campaign.user.domain_id)
        domain_name = domain.name.lower()
        if 'gettalent' in domain_name or 'bluth' in domain_name or 'dice' in domain_name:
            to_address = campaign.user.email
        else:
            to_address = app.config[TalentConfigKeys.GT_GMAIL_ID]

    email_client_credentials_id = campaign.email_client_credentials_id
    if email_client_credentials_id:  # In case user wants to send email-campaign via added SMTP server.
        try:
            email_client_credentials = campaign.email_client_credentials
            decrypted_password = decrypt_password(email_client_credentials.password)
            client = SMTP(email_client_credentials.host, email_client_credentials.port,
                          email_client_credentials.email, decrypted_password)
            client.send_email(to_address, subject, new_text)
        except Exception as error:
            logger.exception('Error occurred while sending campaign via SMTP server. Error:%s' % error.message)
            return False
    else:
        try:
            default_email = get_default_email_info()['email']
            email_response = send_email(source='"%s" <%s>' % (campaign._from, default_email),
                                        # Emails will be sent from verified email by Amazon SES for respective
                                        #  environment.
                                        subject=subject,
                                        html_body=new_html or None,
                                        # Can't be '', otherwise, text_body will not show in email
                                        text_body=new_text,
                                        to_addresses=to_address,
                                        reply_address=campaign.reply_to.strip(),
                                        # BOTO doesn't seem to work with an array as to_addresses
                                        body=None,
                                        email_format='html' if campaign.body_html else 'text')
        except Exception as e:
            # Mark email as bounced
            _handle_email_sending_error(email_campaign_send, candidate.id, to_address, blast_params,
                                        email_campaign_blast_id, e)
            return False

        username = getpass.getuser()
        # Save SES message ID & request ID
        logger.info('''Marketing email sent successfully.
                       Recipients    : %s,
                       UserId        : %s,
                       System User Name: %s,
                       Environment   : %s,
                       Email Response: %s
                    ''', to_address, user_id, username, app.config[TalentConfigKeys.ENV_KEY], email_response)
        request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
        message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
        email_campaign_send.update(ses_message_id=message_id, ses_request_id=request_id)

    # Create activity in a celery task
    celery_create_activity.delay(campaign.user.id,
                                 Activity.MessageIds.CAMPAIGN_EMAIL_SEND,
                                 email_campaign_send,
                                 dict(campaign_name=campaign.name, candidate_name=candidate.name),
                                 'Could not add `campaign send activity` for email-campaign(id:%s) and User(id:%s)' %
                                 (campaign.id, campaign.user.id))
    return True


@celery_app.task(name='send_email_campaign_to_candidate')
def send_email_campaign_to_candidate(user_id, campaign, candidate_id, candidate_address,
                                     blast_params, email_campaign_blast_id, blast_datetime):
    """
    For each candidate, this function is called to send email campaign to candidate.
    :param user_id: Id of user
    :param campaign: EmailCampaign object
    :param candidate_id: candidate id
    :param candidate_address: candidate email address
    :param blast_params: parameters of email campaign blast
    :param email_campaign_blast_id: email campaign blast object id.
    :param blast_datetime: email campaign blast datetime
    :type campaign: EmailCampaign
    :type candidate_id: int | long
    :type candidate_address: str
    :type blast_params: dict
    :type email_campaign_blast_id: int|long
    :type blast_datetime: datetime
    :rtype bool
    """
    raise_if_not_positive_int_or_long(user_id)
    raise_if_not_instance_of(campaign, EmailCampaign)
    raise_if_not_positive_int_or_long(candidate_id)
    raise_if_not_instance_of(candidate_address, basestring)
    raise_if_not_instance_of(blast_params, dict)
    raise_if_not_positive_int_or_long(email_campaign_blast_id)
    raise_if_not_instance_of(blast_datetime, datetime)

    with app.app_context():
        logger.info('sending campaign to candidate(id:%s).' % candidate_id)
        try:
            result_sent = send_campaign_emails_to_candidate(
                user_id=user_id,
                campaign_id=campaign.id,
                candidate_id=candidate_id,
                # candidates.find(lambda row: row.id == candidate_id).first(),
                candidate_address=candidate_address,
                blast_params=blast_params,
                email_campaign_blast_id=email_campaign_blast_id,
                blast_datetime=blast_datetime
            )
            return result_sent
        except Exception as error:
            logger.exception('Error while sending email campaign(id:%s) to candidate(id:%s). Error is: %s'
                             % (campaign.id, candidate_id, error.message))
            db.session.rollback()
            return False


def get_new_text_html_subject_and_campaign_send(campaign_id, candidate_id, candidate_address, blast_params=None,
                                                email_campaign_blast_id=None, blast_datetime=None):
    """
    This gets new_html and new_text by URL conversion method and returns
    new_html, new_text, subject, email_campaign_send, blast_params, candidate.
    :param campaign_id: EmailCampaign object id
    :param candidate_id: id of candidate
    :param blast_params: email_campaign blast params
    :param email_campaign_blast_id:  email campaign blast id
    :param blast_datetime: email campaign blast datetime
    :param candidate_address: Address of Candidate
    :type campaign_id: int | long
    :type candidate_id: int | long
    :type blast_params: dict | None
    :type email_campaign_blast_id: int | long | None
    :type blast_datetime: datetime.datetime | None
    :type candidate_address: basestring
    """
    raise_if_not_positive_int_or_long(campaign_id)
    raise_if_not_positive_int_or_long(candidate_id)

    if blast_params:
        raise_if_not_instance_of(blast_params, dict)
    if email_campaign_blast_id:
        raise_if_not_positive_int_or_long(email_campaign_blast_id)
    if blast_datetime:
        raise_if_not_instance_of(blast_datetime, datetime)

    # TODO: We should solve that detached instance issue more gracefully.
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
        blast_datetime = datetime.utcnow()
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
    logger.info('get_new_text_html_subject_and_campaign_send: candidate_id: %s' % candidate.id)

    # Perform MERGETAG replacements
    [new_html, new_text, subject] = do_mergetag_replacements([new_html, new_text, campaign.subject],
                                                             candidate, candidate_address)
    # Perform URL conversions and add in the custom HTML
    logger.info('get_new_text_html_subject_and_campaign_send: email_campaign_send_id: %s' % email_campaign_send.id)
    new_text, new_html = create_email_campaign_url_conversions(new_html=new_html,
                                                               new_text=new_text,
                                                               is_track_text_clicks=campaign.is_track_text_clicks,
                                                               is_track_html_clicks=campaign.is_track_html_clicks,
                                                               custom_url_params_json=campaign.custom_url_params_json,
                                                               is_email_open_tracking=campaign.is_email_open_tracking,
                                                               custom_html=campaign.custom_html,
                                                               email_campaign_send_id=email_campaign_send.id)
    return new_text, new_html, subject, email_campaign_send, blast_params, candidate


def _handle_email_sending_error(email_campaign_send, candidate_id, to_addresses, blast_params,
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
                     % (candidate_id, to_addresses))


def update_hit_count(url_conversion):
    try:
        # Increment hit count for email marketing
        new_hit_count = (url_conversion.hit_count or 0) + 1
        url_conversion.hit_count = new_hit_count
        url_conversion.last_hit_time = datetime.utcnow()
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
            # Create activity in a celery task
            celery_create_activity.delay(candidate.user_id,
                                         Activity.MessageIds.CAMPAIGN_EMAIL_OPEN if is_open
                                         else Activity.MessageIds.CAMPAIGN_EMAIL_CLICK,
                                         email_campaign_send,
                                         dict(candidateId=candidate.id,
                                              campaign_name=email_campaign_send.email_campaign.name,
                                              candidate_name=candidate.formatted_name),
                                         'Error occurred while creating activity for email-campaign(id:%s) '
                                         'open/click.' % email_campaign_send.campaign_id
                                   )

            logger.info("Activity is being added for URL redirect for candidate(id:%s). "
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
    :param candidate_id: id of candidate.
    :type candidate_id: bool
    :rtype int | None
    """
    raise_if_not_positive_int_or_long(candidate_id)
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
    :type blast_id: int | long
    :type new_sends: int
    :type campaign: EmailCampaign
    :type new_candidates_only: bool
    """
    raise_if_not_positive_int_or_long(blast_id)
    raise_if_not_instance_of(new_sends, int)
    raise_if_not_instance_of(new_candidates_only, bool)
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError(error_message='Valid campaign object must be provided')

    blast_obj = EmailCampaignBlast.get_by_id(blast_id)
    blast_obj.update(sends=blast_obj.sends + new_sends)
    # This will be needed later
    # update_candidate_document_on_cloud(user, candidate_ids_and_emails)
    logger.info("Marketing email batch completed, emails sent=%s, "
                "campaign_name=%s, campaign_id=%s, user=%s, new_candidates_only=%s",
                new_sends, campaign.name, campaign.id, campaign.user.email, new_candidates_only)


def _update_blast_unsubscribed_candidates(blast_id, unsubscribed_candidates):
    """
    This updates the email campaign blast object with number of unsubscribed candidates.
    :param blast_id: Id of blast object.
    :param unsubscribed_candidates: Number of new sends.
    :type blast_id: int | long
    :type unsubscribed_candidates: int
    """
    raise_if_not_positive_int_or_long(blast_id)
    raise_if_not_instance_of(unsubscribed_candidates, int)

    blast_obj = EmailCampaignBlast.get_by_id(blast_id)
    blast_obj.update(unsubscribed_candidates=unsubscribed_candidates)


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

    send_obj = None
    # get the corresponding EmailCampaignSend object that is associated with given AWS message id
    for _ in retrier(sleeptime=2, sleepscale=1, attempts=15):
        EmailCampaignSend.session.commit()
        send_obj = EmailCampaignSend.get_by_amazon_ses_message_id(message_id)
        if send_obj:  # found email campaign send, no need to retry
            break

    if not send_obj:
        logger.info("""Unable to find email campaign send for this email bounce.
                       MessageId: %s
                       Emails: %s
                       Bounce: %s""", message_id, emails, bounce)

    # Mark the send object as bounced.
    else:
        send_obj.update(is_ses_bounce=True)
        blast = EmailCampaignBlast.get_by_send(send_obj)

        if not blast:
            logger.error('Unable to find email campaign blast associated with email campaign send (id:%s).'
                         '\nBounce Message: %s', send_obj.id, bounce)
        # increase number of bounces by one for associated campaign blast.
        else:
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
    if bounce['bounceType'] == aws.PERMANENT_BOUNCE:
        # Mark the matching emails as bounced in all domains because an email that is invalid
        # would be invalid in all domains.
        CandidateEmail.mark_emails_bounced(emails)
        logger.info('Marked %s email addresses as bounced' % emails)
    elif bounce['bounceType'] == aws.TEMPORARY_BOUNCE:
        logger.info('Email was bounced as Transient. '
                    'We will not mark it bounced because it is a temporary problem')


def get_candidates_from_smartlist_for_email_client_id(campaign, list_ids):
    """
    Get candidates from smartlist in case client id is provided. It is a separate function
    because in case client id is provided, the candidate retrieving process needs not to
    be sent on celery.
    :param campaign: Valid EmailCampaign object.
    :param list_ids: List of smartlist ids associated with campaign.
    :type campaign: EmailCampaign
    :type list_ids: list
    :return: List of candidate ids.
    :rtype list
    """
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError("Valid email campaign must be provided.")
    if not isinstance(list_ids, list) or len(list_ids) <= 0:
        raise InternalServerError("Please provide list of smartlist ids.")
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


def get_subscribed_and_unsubscribed_candidates_ids(campaign, all_candidate_ids, new_candidates_only=False):
    """
    Takes campaign and all candidate ids as arguments and process them to return
    the ids of subscribed and unsubscribed candidates.
    :param campaign: email campaign
    :param all_candidate_ids: ids of all candidates to whome we are going to send campaign
    :param new_candidates_only: if campaign is to be sent only to new candidates
    :type campaign: EmailCampaign
    :type all_candidate_ids: list
    :type new_candidates_only: bool
    :return ids of subscribed and unsubscribed candidates
    :rtype tuple
    """
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError(error_message='Valid EmailCampaign object must be provided.')
    if not isinstance(all_candidate_ids, list) or len(all_candidate_ids) < 0:
        raise InternalServerError(error_message='all_candidates_ids must be provided')
    if not isinstance(new_candidates_only, bool):
        raise InternalServerError(error_message='new_candidates_only must be bool')
    unsubscribed_candidates_ids = []
    if campaign.is_subscription:
        # A subscription campaign is a campaign which needs candidates
        # to be subscribed to it in order to receive notifications regarding the campaign.
        # If the campaign is a subscription campaign,
        # only get candidates subscribed to the campaign's frequency.
        subscribed_candidate_ids = CandidateSubscriptionPreference.get_subscribed_candidate_ids(campaign,
                                                                                                all_candidate_ids)
        unsubscribed_candidates_ids = list(set(all_candidate_ids) - set(subscribed_candidate_ids))
        if not subscribed_candidate_ids:
            logger.error("No candidates in subscription campaign %s", campaign)

    else:
        # Otherwise, just filter out unsubscribed candidates:
        # their subscription preference's frequencyId is NULL, which means 'Never'

        for candidate_id in all_candidate_ids:
            # Call candidate API to get candidate's subscription preference.
            subscription_preference = get_candidate_subscription_preference(candidate_id, campaign.user.id)
            # campaign_subscription_preference = get_subscription_preference(candidate_id)
            logger.debug("subscription_preference: %s" % subscription_preference)
            if subscription_preference and not subscription_preference.get('frequency_id'):
                unsubscribed_candidates_ids.append(candidate_id)

        # Remove un-subscribed candidates
        subscribed_candidate_ids = list(set(all_candidate_ids) - set(unsubscribed_candidates_ids))
    # If only getting candidates that haven't been emailed before...
    if new_candidates_only:
        emailed_candidate_ids = EmailCampaignSend.get_already_emailed_candidates(campaign)

        # Filter out already emailed candidates from subscribed_candidate_ids, so we have new candidate_ids only
        new_candidate_ids = list(set(subscribed_candidate_ids) - set(emailed_candidate_ids))
        # assign it to subscribed_candidate_ids (doing it explicit just to make it clear)
        subscribed_candidate_ids = new_candidate_ids
    # Logging info of unsubscribed candidates.
    logger.info("Email campaign id is: %s. Number of unsubscribed candidates: %s. Unsubscribed candidate's ids are:"
                " %s" % (campaign.id, len(unsubscribed_candidates_ids), unsubscribed_candidates_ids))
    return subscribed_candidate_ids, unsubscribed_candidates_ids


def get_smartlist_candidates_via_celery(user_id, campaign_id, smartlist_ids, new_candidates_only=False):
    """
    Get candidates of given smartlist by creating celery task for each smartlist.
    :param user_id: ID of user
    :param campaign_id: Email Campaign ID
    :param smartlist_ids: List of smartlist ids associated with given campaign
    :param new_candidates_only: True if only new candidates are to be returned.
    :type user_id: int | long
    :type campaign_id: int | long
    :type new_candidates_only: bool
    :type smartlist_ids: list
    :returns list of smartlist candidates
    :rtype list
    """
    raise_if_not_positive_int_or_long(user_id)
    raise_if_not_positive_int_or_long(campaign_id)
    raise_if_not_instance_of(new_candidates_only, bool)

    campaign = EmailCampaign.get_by_id(campaign_id)
    campaign_type = campaign.__tablename__

    # Get candidates present in each smartlist
    tasks = [get_candidates_from_smartlist.subtask(
        (list_id, True, user_id),
        link_error=celery_error_handler(
            campaign_type), queue=campaign_type) for list_id in smartlist_ids]

    # Register function to be called after all candidates are fetched from smartlists
    callback = process_campaign_send.subtask((user_id, campaign_id, smartlist_ids, new_candidates_only, ),
                                             queue=campaign_type)
    # This runs all tasks asynchronously and sets callback function to be hit once all
    # tasks in list finish running without raising any error. Otherwise callback
    # results in failure status.
    chord(tasks)(callback)


def notify_and_get_blast_params(campaign, new_candidates_only, candidate_ids_and_emails):
    """
    Notifies admins that email campaign is about to be sent shortly. Also returns blast params
    for the intended campaign.
    :param campaign: Email Campaign
    :param new_candidates_only: True if campaign needs to be sent to new candidates only.
    :param candidate_ids_and_emails: Ids and email addresses of candidates.
    :type campaign: EmailCampaign
    :type new_candidates_only: bool
    :type candidate_ids_and_emails: list
    :return:
    """
    if not isinstance(campaign, EmailCampaign):
        raise InternalServerError('Valid EmailCampaign object must be provided.')
    if not candidate_ids_and_emails:
        raise InternalServerError(error_message='Candidate data not provided')
    with app.app_context():
        email_notification_to_admins(
            subject='Marketing batch about to send',
            body="Marketing email batch about to send, campaign.name=%s, campaign.id=%s, user=%s, "
                 "new_candidates_only=%s, address list size=%s"
                 % (campaign.name, campaign.id, campaign.user.email, new_candidates_only,
                    len(candidate_ids_and_emails))
                )
        logger.info("Marketing email batch about to send, campaign.name=%s, campaign.id=%s, user=%s, "
                    "new_candidates_only=%s, address list size=%s"
                    % (campaign.name, campaign.id, campaign.user.email, new_candidates_only,
                        len(candidate_ids_and_emails)))
    # Create activity in a celery task
    celery_create_activity.delay(campaign.user.id, Activity.MessageIds.CAMPAIGN_SEND, campaign,
                                 dict(id=campaign.id, name=campaign.name,
                                      num_candidates=len(candidate_ids_and_emails)),
                                 'Error occurred while creating activity for email-campaign(id:%s) batch send.'
                                 % campaign.id
                                 )
    # Create the email_campaign_blast for this blast
    blast_datetime = datetime.utcnow()
    email_campaign_blast = EmailCampaignBlast(campaign_id=campaign.id,
                                              sent_datetime=blast_datetime)
    EmailCampaignBlast.save(email_campaign_blast)
    blast_params = dict(sends=0, bounces=0)
    return email_campaign_blast.id, blast_params, blast_datetime


@celery_app.task(name='celery_error_handler')
def celery_error_handler(uuid):
    """
    This method is invoked whenever some error occurs.
    It rollbacks the transaction otherwise it will cause other transactions (if any) to fail.
    :param uuid:
    """
    db.session.rollback()


@celery_app.task(name='create_activity')
def celery_create_activity(user_id, _type, source, params, error_message="Error occurred while creating activity"):
    """
    This method creates activity for campaign create, delete, schedule etc. in a celery task.
    :param int | long user_id: id of user
    :param int _type: type of activity
    :param db.Model source: source object. Basically it will be Model object.
    :param dict params: activity params
    :param string error_message: error message to show in case of any exception
    """
    try:
        # Add activity
        CampaignBase.create_activity(user_id, _type, source, params)
    except Exception as e:
        logger.exception('%s\nError: %s' % (error_message, e.message))


def send_test_email(user, request):
    """
    This function sends a test email to given email addresses. Email sender depends on environment:
        - local-no-reply@gettalent.com for dev
        - staging-no-rely@gettalent.com for staging
        - no-reply@gettalent.com for Prod
    :param user: User model object (current user)
    :param request: Flask request object
    """
    # Get and validate request data
    data = get_json_data_if_validated(request, TEST_EMAIL_SCHEMA)
    body_text = data.get('body_text', '')
    [new_html, new_text, subject] = do_mergetag_replacements([data['body_html'], body_text, data['subject']],
                                                             request.user)
    try:
        default_email = get_default_email_info()['email']
        send_email(source='"%s" <%s>' % (data['from'], default_email),
                   subject=subject,
                   html_body=new_html or None,
                   # Can't be '', otherwise, text_body will not show in email
                   text_body=new_text,
                   to_addresses=data['email_address_list'],
                   reply_address=user.email,
                   body=None,
                   email_format='html')
        logger.info('Test email has been sent to %s addresses. User(id:%s)'
                    % (data['email_address_list'], request.user.id))
    except Exception as e:
        logger.error('Error occurred while sending test email. Error: %s', e)
        raise InternalServerError('Unable to send emails to test email addresses:%s.' % data['email_address_list'])

