"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

   This module contains functions used by campaign services. e.g. sms_campaign_service etc.
We have CampaignUtils class here which contains following methods:

We also have some functions here like
    - get_model() etc.
"""

# Standard Imports
import os
import importlib
from datetime import datetime

# Third Party
from dateutil.tz import tzutc
from flask import current_app
from ska import (sign_url, Signature)

# Database Models

from ..models.db import db
from ..models.misc import Activity
from ..models.email_campaign import EmailCampaign, EmailCampaignBlast, EmailCampaignSend
from ..models.sms_campaign import (SmsCampaign, SmsCampaignSmartlist, SmsCampaignBlast,
                                   SmsCampaignSend)
from ..models.push_campaign import (PushCampaign, PushCampaignBlast, PushCampaignSmartlist,
                                    PushCampaignSend)

# Common Utils
from ..routes import SchedulerApiUrl
from ..utils.datetime_utils import DatetimeUtils
from ..talent_config_manager import TalentConfigKeys, TalentEnvs
from ..error_handling import (InvalidUsage, ResourceNotFound)
from .validators import raise_if_dict_values_are_not_int_or_long
from ..utils.handy_functions import (http_request, snake_case_to_pascal_case)
from ..utils.validators import raise_if_not_instance_of


def _get_campaign_type_prefix(campaign_type):
    """
    Campaign type can be 'sms_campaign', 'push_campaign' etc. So this method checks if campaign
    type is SMS, it returns SMS. Otherwise it returns prefix as lower case e.g push or email.
    :param campaign_type:
    :type campaign_type: str
    :return:
    """
    raise_if_not_instance_of(campaign_type, basestring)
    prefix = campaign_type.split('_')[0]
    if prefix in [SmsCampaign.__tablename__]:
        return prefix.upper()
    return prefix.lower()


class CampaignUtils(object):
    """
    This is the class which contains methods used for campaign services.
    """
    # Any campaign service will add the entry of respective model name here
    SMS = SmsCampaign.__tablename__
    PUSH = PushCampaign.__tablename__
    EMAIL = EmailCampaign.__tablename__

    # Any campaign service will add the entry of respective model name here
    MODELS = (SmsCampaign, EmailCampaign, PushCampaign)
    SMARTLIST_MODELS = (SmsCampaignSmartlist, PushCampaignSmartlist)
    BLAST_MODELS = (SmsCampaignBlast, EmailCampaignBlast, PushCampaignBlast)
    SEND_MODELS = (SmsCampaignSend, EmailCampaignSend, PushCampaignSend)
    NAMES = (SMS, EMAIL, PUSH)
    # This contains campaign types for which we need to append 'an' in activity message.
    # e.g. 'John' created an SMS campaign
    WITH_ARTICLE_AN = [_get_campaign_type_prefix(item).lower() for item in [SMS, EMAIL, PUSH]]
    # This variable is used for sms_campaign_service. In case of 'dev', 'jenkins' or 'qa', our
    # Twilio's account should not be charged while purchasing a number or sending SMS to candidates.
    # This is set to False in case of 'prod'.
    # Also in case of dev/qa/Jenkins we do not want Emails and SMS to be sent to candidates, so
    # this variable is used there as well.
    IS_DEV = False if os.getenv(TalentConfigKeys.ENV_KEY) == TalentEnvs.PROD else True

    @classmethod
    def get_campaign_type_prefix(cls, campaign_type):
        """
        Campaign type can be 'sms_campaign', 'push_campaign' etc. So this method checks if campaign
        type is SMS, it returns SMS. Otherwise it returns prefix as lower case e.g push or email.
        :param campaign_type:
        :type campaign_type: str
        :return:
        """
        cls.raise_if_not_valid_campaign_type(campaign_type)
        return _get_campaign_type_prefix(campaign_type)

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
        raise_if_not_instance_of(campaign_type, basestring)
        if campaign_type not in CampaignUtils.NAMES:
            raise InvalidUsage('%s is not a valid campaign type. Valid types are %s'
                               % (campaign_type, CampaignUtils.NAMES))

    @classmethod
    def get_send_obj_by_blast_id_and_candidate_id(cls, model, blast_id, candidate_id):
        """
        This gets the campaign_send object (e.g object of SmsCampaignSend or PushCampaignSend etc.)
        by querying blast_id and candidate_id.
        """
        raise_if_dict_values_are_not_int_or_long(dict(blast_id=blast_id,
                                                      candidate_id=candidate_id
                                                      ))
        return model.query.filter_by(blast_id=blast_id, candidate_id=candidate_id).first()

    @classmethod
    def update_blast(cls, blast_obj, data):
        """
        This gets the campaign_send object (e.g object of SmsCampaignSend or PushCampaignSend etc.)
        by querying blast_id and candidate_id.
        """
        raise_if_not_instance_of(blast_obj, cls.BLAST_MODELS)
        blast_obj.query.filter_by(id=blast_obj.id).update(data)
        db.session.commit()

    @classmethod
    def get_send_url_con_obj_by_send_id_and_url_conversion_id(cls, model, send_id,
                                                              url_conversion_id):
        """
        This gets the campaign_send_url_conversion object (e.g object of
        SmsCampaignSendUrlConversion  or PushCampaignSendUrlConversion etc.) by querying send_id
        and candidate_id.
        """
        raise_if_dict_values_are_not_int_or_long(dict(send_id=send_id,
                                                      url_conversion_id=url_conversion_id))
        return model.query.filter_by(send_id=send_id,
                                     url_conversion_id=url_conversion_id).first()

    @classmethod
    def get_campaign_smartlist_obj_by_campaign_and_smartlist_id(cls, model, campaign_id,
                                                                smartlist_id):
        """
        This gets the campaign_smartlist object (e.g object of SmsCampaignSmartlist or
        PushCampaignSmartlist etc.) by querying campaign_id and smartlist_id.
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id,
                                                      smartlist_id=smartlist_id))
        return model.query.filter_by(campaign_id=campaign_id, smartlist_id=smartlist_id).first()

    @classmethod
    def get_campaign_smartlist_obj_by_campaign_id(cls, model, campaign_id):
        """
        This gets all the campaign_smartlist objects (e.g object of SmsCampaignSmartlist or
        PushCampaignSmartlist etc.) by querying campaign_id.
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        return model.query.filter_by(campaign_id=campaign_id).all()

    @classmethod
    def get_send_url_conversion_obj_by_url_conversion_id(cls, model, url_conversion_id):
        """
        This gets campaign_send_url_conversion (e.g. object of SmsCampaignSendUrlConversion object)
        object from url_conversion_id.
        :param model:
        :param url_conversion_id:
        :return:
        """
        return model.query.filter_by(url_conversion_id=url_conversion_id).first()

    @classmethod
    def get_send_url_conversion_model(cls, campaign_type):
        """
        This gets the campaign_send_url_conversion model for respective campaign.
        e.g. SmsCampaignSendUrlConversion model etc.
        :param campaign_type:
        :return:
        """
        cls.raise_if_not_valid_campaign_type(campaign_type)
        return get_model(campaign_type, campaign_type + '_send_url_conversion')

    @staticmethod
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
        CampaignUtils.raise_if_not_valid_campaign_type(campaign_name)
        raise_if_not_instance_of(postfix, basestring)
        return "_".join(campaign_name.split('_')[::-1]).upper() + '_' + postfix

    @staticmethod
    def get_activity_message_id(activity_name):
        """
        Activity messages have names and ids. e.g. CAMPAIGN_SEND = 6.
        So we pass here CAMPAIGN_SEND and it will give us 6.
        For a given message name, we get the its id from class Activity.MessageIds.
        :param activity_name: e.g. CAMPAIGN_SMS_CLICK or CAMPAIGN_PUSH_CLICK
        :type activity_name: str
        :exception:  Invalid Usage
        :return: activity type
        :rtype: int
        """
        raise_if_not_instance_of(activity_name, basestring)
        if not hasattr(Activity.MessageIds, activity_name):
            raise InvalidUsage('Unknown activity message id %s.' % activity_name)
        message_id = getattr(Activity.MessageIds, activity_name)
        if not message_id:
            raise InvalidUsage('No Activity message %s found for id.' % activity_name)
        return message_id

    @classmethod
    def get_activity_message_id_from_name(cls, activity_name):
        """
        From given Activity name, we get the id of that activity message and handle exception
        if any occurs.
        :param activity_name: Name of activity, e.g CAMPAIGN_SMS_CLICK etc.
        :type activity_name: str
        :return: id of activity message
        :rtype: int
        """
        raise_if_not_instance_of(activity_name, basestring)
        try:
            _type = cls.get_activity_message_id(activity_name)
            return _type
        except InvalidUsage:
            current_app.config[TalentConfigKeys.LOGGER].exception(
                'update_stats_and_create_click_activity: Activity type not found for %s. '
                'Cannot create click activity' % activity_name)

    @staticmethod
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
        return sign_url(auth_user='no_user',
                        secret_key=current_app.config[TalentConfigKeys.SECRET_KEY],
                        url=redirect_url,
                        valid_until=DatetimeUtils.unix_time(end_datetime.replace(tzinfo=tzutc())))

    @staticmethod
    def if_valid_signed_url(request_args):
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
                                            secret_key=current_app.config[
                                                TalentConfigKeys.SECRET_KEY])

    @staticmethod
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
            base_class.create_campaign_send_activity(user_id, campaign, total_sends)
        logger.debug('post_campaign_sent_processing: %s(id:%s) has been sent to %s candidate(s).'
                     '(User(id:%s))' % (campaign_type, campaign.id, total_sends, user_id))

    @staticmethod
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

    @staticmethod
    def get_campaign(campaign_id, current_user_id, campaign_type):
        """
        This function gets the campaign from database table as specified by campaign_type.
        If campaign obj is found, it returns it. Otherwise it returns ResourceNotFound error.
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
            raise ResourceNotFound('%s(id=%s) not found.' % (campaign_type, campaign_id))
        return campaign_obj


def get_model(file_name, model_name, service_name=None):
    """
    This function is used to import module from given parameters.
    e.g. if we want to import SmsCampaign database model, we will provide
        file_name='sms_campaign' and model_name ='SmsCampaign'
    :param file_name: Name of file from which we want to import some model
    :param model_name: Name of model we want to import
    :param service_name: Name of service. e.g. sms_campaign_service etc
    :type file_name: str
    :type model_name: str
    :type service_name: str
    :exception: Invalid usage
    :exception: AttributeError
    :exception: ImportError
    :return: import the required class and return it
    """
    raise_if_not_instance_of(file_name, basestring)
    raise_if_not_instance_of(model_name, basestring)
    logger = current_app.config[TalentConfigKeys.LOGGER]
    model_name = snake_case_to_pascal_case(model_name)
    if service_name:
        raise_if_not_instance_of(model_name, basestring)
        module_name = service_name + '_service.common.models.' + file_name
    else:
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
