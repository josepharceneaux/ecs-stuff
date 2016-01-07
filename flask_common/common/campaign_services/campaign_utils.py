"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

   This module contains functions used by campaign services. e.g. sms_campaign_service etc.
"""

# Standard Imports
import importlib
from datetime import datetime

# Third Party
from pytz import timezone
from dateutil.tz import tzutc
from flask import current_app
from ska import sign_url, Signature

# Application Specific
from ..models.misc import UrlConversion
from ..error_handling import InvalidUsage
from ..models.sms_campaign import SmsCampaign
from ..models.push_campaign import PushCampaign
from ..talent_config_manager import TalentConfigKeys
from ..utils.activity_utils import ActivityMessageIds
from ..utils.handy_functions import snake_case_to_pascal_case


class CampaignType(object):
    """
    This is the class to avoid global variables for names of campaign
    """
    SMS = SmsCampaign.__tablename__
    PUSH = PushCampaign.__tablename__


class FrequencyIds(object):
    """
    This is the class to avoid global variables for following names.
    These variables show the frequency_id associated with type of schedule.
    """
    ONCE = 1
    DAILY = 2
    WEEKLY = 3
    BIWEEKLY = 4
    MONTHLY = 5
    YEARLY = 6


def frequency_id_to_seconds(frequency_id):
    """
    This gives us the number of seconds for given frequency_id.
    frequency_id is in range 1 to 6 representing
        'Once', 'Daily', 'Weekly', 'Biweekly', 'Monthly', 'Yearly'
    respectively.
    :param frequency_id: int
    :return: seconds
    :rtype: int
    """
    if not frequency_id:
        return 0
    if not isinstance(frequency_id, int):
        raise InvalidUsage('Include frequency id as int')
    seconds_from_frequency_id = {
        FrequencyIds.ONCE: 0,
        FrequencyIds.DAILY: 24 * 3600,
        FrequencyIds.WEEKLY: 7 * 24 * 3600,
        FrequencyIds.BIWEEKLY: 14 * 24 * 3600,
        FrequencyIds.MONTHLY: 30 * 24 * 3600,
        FrequencyIds.YEARLY: 365 * 24 * 3600
    }
    seconds = seconds_from_frequency_id.get(frequency_id)
    if not seconds and seconds != 0:
        raise InvalidUsage("Unknown frequency ID: %s" % frequency_id)
    return seconds


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
    epoch = datetime(1970, 1, 1, tzinfo=timezone('UTC'))
    delta = dt - epoch
    return delta.total_seconds()


def get_model(file_name, model_name):
    """
    This function is used to import module from given parameters.
    e.g. if we want to import SmsCampaign database model, we will provide
        file_name='sms_campaign' and model_name ='SmsCampaign'
    :param file_name: Name of file from which we want to import some model
    :param model_name: Name of model we want to import
    :return: import the required class and return it
    """
    module_name = file_name + '_service.common.models.' + file_name
    try:
        module = importlib.import_module(module_name)
        _class = getattr(module, model_name)
    except ImportError:
        current_app.config['LOGGER'].exception('Error importing model %s' % model_name)
        raise
    except AttributeError:
        current_app.config['LOGGER'].exception('%s has no attribute %s' % (file_name, model_name))
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
    if not getattr(ActivityMessageIds, activity_name):
        raise InvalidUsage('No Activity message %s found for id.' % activity_name)
    return getattr(ActivityMessageIds, activity_name)


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
        current_app.config['LOGGER'].exception(
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
    campaign_send_obj = getattr(campaign_send_url_conversion_obj, 'send')
    # get campaign_blast object
    campaign_blast_obj = getattr(campaign_send_obj, 'blast')
    # get candidate object
    candidate_obj = getattr(campaign_send_obj, 'candidate')
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


def processing_after_campaign_sent(base_class, sends_result, user_id, campaign_type, blast_id,
                                   auth_header):
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
    :param auth_header: auth header of current user to make HTTP request to other services
    :type base_class: CampaignBase
    :type sends_result: list
    :type user_id: int
    :type campaign_type: str
    :type blast_id: int
    :type auth_header: dict

    **See Also**
        .. see also:: callback_campaign_sent() method in SmsCampaignBase class inside
                        sms_campaign_service/sms_campaign_base.py
    """
    if isinstance(sends_result, list):
        total_sends = sends_result.count(True)
        blast_model = get_model(campaign_type, snake_case_to_pascal_case(campaign_type) + 'Blast')
        blast_obj = blast_model.get_by_id(blast_id)
        if not blast_obj:
            current_app.config['LOGGER'].error(
                    'callback_campaign_sent: Blast object was not found with id %s' % blast_id)
        campaign = blast_obj.campaign
        if total_sends:
            # update SMS campaign blast. i.e. update number of sends.
            try:
                blast_obj.update(sends=blast_obj.sends+total_sends)
            except Exception:
                current_app.config['LOGGER'].exception(
                    'callback_campaign_sent: Error updating campaign(id:%s) blast(id:%s)'
                    % (campaign.id, blast_obj.id))
                raise
            base_class.create_campaign_send_activity(user_id, campaign,
                                                     auth_header, total_sends)
        current_app.config['LOGGER'].debug(
            'process_send: %s(id:%s) has been sent to %s candidate(s).'
            '(User(id:%s))' % (campaign_type, campaign.id, total_sends, user_id))
    else:
        current_app.config['LOGGER'].error('callback_campaign_sent: Result is not a list')
