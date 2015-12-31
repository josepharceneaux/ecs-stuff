"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

   This module contains functions used by campaign services. e.g. sms_campaign_service etc.
"""

# Standard Imports
from datetime import datetime

# Application Specific
from ..error_handling import InvalidUsage


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
