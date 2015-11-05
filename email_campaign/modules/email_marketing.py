from email_campaign.common.error_handling import UnprocessableEntity
from ..models.email_marketing import EmailCampaign, EmailCampaignSmartList
from common.models.db import db
from common.models.misc import Frequency
from common.error_handling import *

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
        schedule_email_campaign.delay()
    # If campaign to be sent in future
    scheduler_task_id = schedule_task(function_name='email_campaign_scheduled',
                                      function_vars=function_vars,
                                      start_time=start_time,
                                      stop_time=stop_time,
                                      period=period, repeats=repeats)
    campaign.update_record(schedulerTaskIds=[scheduler_task_id])


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
