"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for campaign services.
"""

# Standard Imports
import re
from datetime import datetime

# Common utils
from ..error_handling import InvalidUsage
from ..utils.common_functions import JSON_CONTENT_TYPE_HEADER


def validate_header(request):
    """
    Proper header should be {'content-type': 'application/json'} for POSTing
    some data on SMS campaign API.
    If header of request is not proper, it raises InvalidUsage exception
    :return:
    """
    if not request.headers.get('CONTENT_TYPE') == JSON_CONTENT_TYPE_HEADER['content-type']:
        raise InvalidUsage(error_message='Invalid header provided')

def validate_datetime_format(str_datetime):
    """
    This validates the given datetime is in ISO UTC format or not. Proper format should be like
    '2015-10-08T06:16:55Z'.

    :param str_datetime: str
    :type str_datetime: str
    :exception: Invalid Usage
    :return: True if given datetime is valid, False otherwise.
    :rtype: bool
    """
    utc_pattern = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
    if re.match(utc_pattern, str_datetime):
        return True
    else:
        raise InvalidUsage('Invalid DateTime: Kindly specify UTC datetime in ISO-8601 format '
                           'like 2015-10-08T06:16:55Z. Given Date is %s' % str_datetime)


def to_utc_str(dt):
    """
    This converts given datetime in '2015-10-08T06:16:55Z' format.
    :param dt: given datetime
    :type dt: datetime
    :return: UTC date in str
    :rtype: str
    """
    if isinstance(dt, datetime):
        raise InvalidUsage(error_message='Given param should be datetime obj')
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def is_valid_url_format(url):
    """
    Reference: https://github.com/django/django-old/blob/1.3.X/django/core/validators.py#L42
    """
    regex = re.compile(
        r'^(http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


def frequency_id_to_seconds(frequency_id):
    #  'Once', 'Daily', 'Weekly', 'Biweekly', 'Monthly', 'Yearly'
    if not isinstance(frequency_id, int):
        raise InvalidUsage(error_message='Include frequency id as int')
    if not frequency_id or frequency_id == 1:
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
