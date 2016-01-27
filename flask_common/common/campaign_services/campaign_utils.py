"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

   This module contains functions used by campaign services. e.g. sms_campaign_service etc.
Functions in this file are
    - frequency_id_to_seconds()
    - to_utc_str()
    - unix_time()
    - get_model()
    - get_activity_message_name() etc.
"""

# Standard Imports
import importlib
from datetime import datetime

# Third Party
from dateutil.tz import tzutc
from flask import current_app
from ska import (sign_url, Signature)

# Database Models
from ..models.misc import UrlConversion
from ..models.email_marketing import EmailCampaign, EmailCampaignBlast
from ..models.sms_campaign import (SmsCampaign, SmsCampaignSmartlist, SmsCampaignBlast)

# Common Utils
from ..routes import SchedulerApiUrl
from ..talent_config_manager import TalentConfigKeys
from ..utils.activity_utils import ActivityMessageIds
from ..error_handling import (InvalidUsage, ResourceNotFound)
from ..utils.handy_functions import snake_case_to_pascal_case
from .validators import raise_if_dict_values_are_not_int_or_long
from ..utils.handy_functions import (http_request, raise_if_not_instance_of)


def get_campaign_type_prefix(campaign_type):
    """
    Campaign type can be 'sms_campaign', 'push_campaign' etc. So this method checks if campaign
    type is SMS, it returns SMS. Otherwise it returns prefix as lower case e.g push or email.
    :param campaign_type:
    :type campaign_type: str
    :return:
    """
    prefix = campaign_type.split('_')[0]
    if prefix in [SmsCampaign.__tablename__]:
        return prefix.upper()
    return prefix.lower()


class CampaignUtils(object):
    """
    This is the class to avoid global variables for names of campaign
    """
    SMS = SmsCampaign.__tablename__
    EMAIL = EmailCampaign.__tablename__
    # TODO: add comment
    WITH_ARTICLE_AN = [get_campaign_type_prefix(item).lower() for item in [SMS, EMAIL]]
    # Any campaign service will add the entry of respective model name here
    MODELS = (SmsCampaign, EmailCampaign)
    SMARTLIST_MODELS = SmsCampaignSmartlist
    BLAST_MODELS = (SmsCampaignBlast, EmailCampaignBlast)
    NAMES = (SMS, EMAIL)

    @classmethod
    def raise_if_not_instance_of_campaign_models(cls, obj):
        """
        This validates that given object is an instance of campaign models. e.g. SmsCampaign,
        PushCampaign etc.
        :param obj: data to validate
        :type obj: SmsCampaign | PushCampaign etc.
        :exception: Invalid Usage
        """
        raise_if_not_instance_of(obj, CampaignUtils.MODELS)

    @classmethod
    def raise_if_not_valid_campaign_type(cls, campaign_type):
        """
        This validates that given campaign_type is a valid type. e.g. 'sms_campaign' or
        'push_campaign' etc.
        :param campaign_type: type of campaign
        :type campaign_type: str
        :exception: Invalid Usage
        """
        raise_if_not_instance_of(campaign_type, str)
        if not campaign_type in CampaignUtils.NAMES:
            raise InvalidUsage('%s is not a valid campaign type. Valid types are %s'
                               % (campaign_type, CampaignUtils.NAMES))



def to_utc_str(dt):
    """
    This converts given datetime in '2015-10-08T06:16:55Z' format.
    :param dt: given datetime
    :type dt: datetime
    :return: UTC date in str
    :rtype: str
    """
    if not isinstance(dt, datetime):
        raise InvalidUsage('Given param should be datetime obj')
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def unix_time(dt):
    """
    Converts dt(UTC) datetime object to epoch in seconds
    :param dt:
    :type dt: datetime
    :return: returns epoch time in milliseconds.
    :rtype: long
    """
    epoch = datetime(1970, 1, 1, tzinfo=tzutc('UTC'))
    delta = dt - epoch
    return delta.total_seconds()


def get_model(file_name, model_name):
    """
    This function is used to import module from given parameters.
    e.g. if we want to import SmsCampaign database model, we will provide
        file_name='sms_campaign' and model_name ='SmsCampaign'
    :param file_name: Name of file from which we want to import some model
    :param model_name: Name of model we want to import
    :type file_name: str
    :type model_name: str
    :exception: Invalid usage
    :exception: AttributeError
    :exception: ImportError
    :return: import the required class and return it
    """
    if not isinstance(file_name, str):
        raise InvalidUsage('file_name must be instance of str.')
    if not isinstance(model_name, str):
            raise InvalidUsage('file_name must be instance of str.')
    logger = current_app.config[TalentConfigKeys.LOGGER]
    model_name = snake_case_to_pascal_case(model_name)
    module_name = file_name + '_service.common.models.' + file_name
    try:
        module = importlib.import_module(module_name)
        _class = getattr(module, model_name)
    except ImportError:
        logger.exception('Error importing model %s.' % model_name)
        raise
    except AttributeError:
        logger.exception('%s has no attribute %s.' % (file_name, model_name))
        raise
    return _class


def get_activity_message_name(campaign_name, postfix):
    """
    This function gets the id of activity message. For example if we want to get id of
    SMS_CAMPAIGN_CLICK, we'll pass campaign_name='sms_campaign' anf postfix='CLICK'
    :param campaign_name: name of campaign in snake_case
    :param postfix: word to be appended
    :type campaign_name: str
    :type postfix: str
    :exception: Invalid usage
    :return: Activity message name
    :rtype: str
    """
    return "_".join(campaign_name.split('_')[::-1]).upper() + '_' + postfix


def get_activity_message_id(activity_name):
    """
    Activity messages have names and ids. e.g. CAMPAIGN_SEND = 6.
    So we pass here CAMPAIGN_SNED and it will give us 6.
    For a given message name, we get the its id from class ActivityMessageIds.
    :param activity_name: e.g. CAMPAIGN_SMS_CLICK or CAMPAIGN_PUSH_CLICK
    :type activity_name: str
    :exception:  Invalid Usage
    :return: activity type
    :rtype: int
    """
    if not hasattr(ActivityMessageIds, activity_name):
        raise InvalidUsage('Unknown activity message id %s.' % activity_name)
    message_id = getattr(ActivityMessageIds, activity_name)
    if not message_id:
        raise InvalidUsage('No Activity message %s found for id.' % activity_name)
    return message_id


def get_activity_message_id_from_name(activity_name):
    """
    From given Activity name, we get the id of that activity message and handle exception
    if any occurs.
    :param activity_name: Name of activity
    :type activity_name: str
    :return: id of activity message
    :rtype: int
    """
    try:
        _type = get_activity_message_id(activity_name)
        return _type
    except InvalidUsage:
        current_app.config[TalentConfigKeys.LOGGER].exception(
            'update_stats_and_create_click_activity: Activity type not found for %s. '
            'Cannot create click activity' % activity_name)


def get_candidate_url_conversion_campaign_send_and_blast_obj(campaign_send_url_conversion_obj):
    """
    Depending on campaign name and CampaignSendUrlConversion (e.g. SmsCampaignSendUrlConversion)
    model, here we get candidate obj, url_conversion obj, campaign_send obj and campaign_blast obj.
    :param campaign_send_url_conversion_obj:
    :type campaign_send_url_conversion_obj: SmsCampaignSendUrlConversion etc
    :return: candidate obj, url_conversion obj, campaign_send obj and campaign_blast obj.
    :rtype: tuple
    """
    # get url_conversion obj
    url_conversion_obj = UrlConversion.get_by_id(campaign_send_url_conversion_obj.url_conversion_id)
    # get campaign_send object
    campaign_send_obj = campaign_send_url_conversion_obj.send
    # get campaign_blast object
    campaign_blast_obj = campaign_send_obj.blast
    # get candidate object
    candidate_obj = campaign_send_obj.candidate
    return candidate_obj, url_conversion_obj, campaign_send_obj, campaign_blast_obj


def sign_redirect_url(redirect_url, end_datetime):
    """
    This function is used to sign the redirect URL (URL to redirect candidate to our app when
    candidate clicks on a URL in SMS campaign or Email campaign etc.)
    This used ska
    :param redirect_url: URL for redirection. e.g. http://127.0.0.1:8012/redirect/1
    :param end_datetime: end_datetime of campaign
    :type redirect_url: str
    :type end_datetime: datetime
    :return:
    """
    if not isinstance(end_datetime, datetime):
        raise InvalidUsage('end_datetime must be instance of datetime')
    return sign_url(auth_user='no_user', secret_key=current_app.config[TalentConfigKeys.SECRET_KEY],
                    url=redirect_url, valid_until=unix_time(end_datetime.replace(tzinfo=tzutc())))


def validate_signed_url(request_args):
    """
    This validates the signed url by checking
    1) if secret_key provided is same as was given at time of signing the URL
    2) valid_until datetime is in future
    3) signature is valid
    4) auth_user is same as was given at the time of signing the URL
    5) extra params are same as were given
    :param request_args: arguments of request
    :return: True if signature is valid, False otherwise
    :rtype: bool
    """
    return Signature.validate_signature(signature=request_args['signature'],
                                        auth_user=request_args['auth_user'],
                                        valid_until=request_args['valid_until'],
                                        extra=request_args['extra'],
                                        secret_key=current_app.config[TalentConfigKeys.SECRET_KEY])


def post_campaign_sent_processing(base_class, sends_result, user_id, campaign_type, blast_id,
                                  oauth_header):
    """
    Once SMS campaign has been sent to all candidates, this function is hit. This is
        a Celery task. Here we

        1) Update number of sends in campaign blast
        2) Add activity e.g. (SMS Campaign "abc" was sent to "1000" candidates")

    :param base_class: CampaignBase class (Need to pass this as import results in circular
                        import issue)
    :param sends_result: Result of executed task
    :param user_id: id of user (owner of campaign)
    :param campaign_type: type of campaign. i.e. sms_campaign or push_campaign
    :param blast_id: id of blast object
    :param oauth_header: auth header of current user to make HTTP request to other services
    :type base_class: CampaignBase
    :type sends_result: list
    :type user_id: int
    :type campaign_type: str
    :type blast_id: int
    :type oauth_header: dict

    **See Also**
        .. see also:: callback_campaign_sent() method in SmsCampaignBase class inside
                        sms_campaign_service/sms_campaign_base.py
    """
    logger = current_app.config[TalentConfigKeys.LOGGER]
    if not isinstance(sends_result, list):
        logger.error("post_campaign_sent_processing: Celery task's result is not a list")
    total_sends = sends_result.count(True)
    blast_model = get_model(campaign_type, campaign_type + '_blast')
    blast_obj = blast_model.get_by_id(blast_id)
    campaign = blast_obj.campaign
    if total_sends:
        # update SMS campaign blast. i.e. update number of sends.
        try:
            blast_obj.update(sends=blast_obj.sends + total_sends)
        except Exception:
            logger.exception(
                'post_campaign_sent_processing: Error updating campaign(id:%s) blast(id:%s)'
                % (campaign.id, blast_obj.id))
            raise
        base_class.create_campaign_send_activity(user_id, campaign,
                                                 oauth_header, total_sends)
    logger.debug('post_campaign_sent_processing: %s(id:%s) has been sent to %s candidate(s).'
                 '(User(id:%s))' % (campaign_type, campaign.id, total_sends, user_id))


def delete_scheduled_task(scheduled_task_id, oauth_header):
    """
    Campaign (e.g. SMS campaign or Push Notification) has a field scheduler_task_id.
    If a campaign was scheduled and user wants to delete that campaign, system should remove
    the task from scheduler_service as well using scheduler_task_id.
    This function is used to remove the job from scheduler_service when someone deletes
    a campaign.
    :return: True if task is not present or has been unscheduled successfully, False otherwise
    :rtype: bool
    """
    logger = current_app.config[TalentConfigKeys.LOGGER]
    if not oauth_header:
        raise InvalidUsage('Auth header is required for deleting scheduled task.')
    if not scheduled_task_id:
        raise InvalidUsage('Provide task id to delete scheduled task from scheduler_service.')
    try:
        response = http_request('DELETE', SchedulerApiUrl.TASK % scheduled_task_id,
                                headers=oauth_header)
        if not response.ok:
            logger.error("delete_scheduled_task: Task(id:%s) couldn't be deleted from "
                         "scheduler_service." % scheduled_task_id)
            return False
    except ResourceNotFound:
        logger.info("delete_scheduled_task: Task(id:%s)has already been removed from "
                    "scheduler_service" % scheduled_task_id)
        return True
    logger.info("delete_scheduled_task: Task(id:%s) has been removed from scheduler_service"
                % scheduled_task_id)
    return True


def get_campaign_for_ownership_validation(campaign_id, current_user_id, campaign_type):
    """
    This function gets the campaign from database table as specified by campaign_type.
    If campaign obj is found, it returns it. Otherwise it returns Resource Not Found error.
    :param campaign_id: id of campaign
    :param current_user_id: id of logged-in user
    :param campaign_type: type of campaign. e.g. sms_campaign or push_campaign
    :type campaign_id: int | long
    :type current_user_id: int | long
    :type campaign_type: str
    :return: campaign obj
    :rtype: SmsCampaign | PushCampaign etc.
    """
    raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id,
                                                  current_user_id=current_user_id))
    CampaignUtils.raise_if_not_valid_campaign_type(campaign_type)
    campaign_model = get_model(campaign_type, campaign_type)
    campaign_obj = campaign_model.query.get(campaign_id)
    if not campaign_obj:
        raise ResourceNotFound('%s(id=%s) not found.' % (campaign_model.__tablename__, campaign_id))
    return campaign_obj
