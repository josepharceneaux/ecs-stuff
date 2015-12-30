"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

   This module contains functions used by campaign services. e.g. sms_campaign_service etc.
"""

# Standard Imports
from datetime import datetime

# Third Party Imports
from pytz import timezone
from dateutil.parser import parse

# Application Specific
from ..error_handling import InvalidUsage
from validators import validate_datetime_format


def frequency_id_to_seconds(frequency_id):
    #  'Once', 'Daily', 'Weekly', 'Biweekly', 'Monthly', 'Yearly'
    if not frequency_id:
        return 0
    if not isinstance(frequency_id, int):
        raise InvalidUsage('Include frequency id as int')
    if frequency_id == 1:
        period = 0
    elif frequency_id == 2:
        period = 24 * 3600
    elif frequency_id == 3:
        period = 7 * 24 * 3600
    elif frequency_id == 4:
        period = 14 * 24 * 3600
    elif frequency_id == 5:
        period = 30 * 24 * 3600
    elif frequency_id == 6:
        period = 365 * 24 * 3600
    else:
        raise InvalidUsage("Unknown frequency ID: %s" % frequency_id)
    return period


def get_utc_datetime_from_str(str_datetime):
    """
    This converts given string datetime into UTC datetime obj.
    This uses validate_datetime_format() to validate the format of given str.
    Valid format should be like 2015-10-08T06:16:55
    :param str_datetime:
    :return: datetime obj
    :rtype: datetime
    """
    if not isinstance(str_datetime, basestring):
        raise InvalidUsage('param should be a string of datetime')
    validate_datetime_format(str_datetime)
    return parse(str_datetime).replace(tzinfo=timezone('UTC'))


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
