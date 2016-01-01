"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

   This module contains functions used by campaign services. e.g. sms_campaign_service etc.
"""

# Standard Imports
import importlib
from datetime import datetime

# Application Specific
from flask import current_app
from ..error_handling import InvalidUsage
from ..utils.activity_utils import ActivityMessageIds


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
    if not seconds_from_frequency_id.get(frequency_id):
        raise InvalidUsage("Unknown frequency ID: %s" % frequency_id)
    return seconds_from_frequency_id.get(frequency_id)


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


def get_activity_type(activity_message_id):
    """
    For a given message id, we get the activity type id from class ActivityMessageIds.
    :param activity_message_id: e.g. CAMPAIGN_SMS_CLICK or CAMPAIGN_PUSH_CLICK
    :type activity_message_id: str
    :exception:  Invalid Usage
    :return: activity type
    :rtype: int
    """
    if not hasattr(ActivityMessageIds, activity_message_id):
        raise InvalidUsage('Unknown activity message id %s.' % activity_message_id)
    if not getattr(ActivityMessageIds, activity_message_id):
        raise InvalidUsage('No Activity message %s found for id.' % activity_message_id)
    return getattr(ActivityMessageIds, activity_message_id)
