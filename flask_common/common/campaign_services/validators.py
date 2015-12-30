"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for campaign services.
"""

# Standard Imports
import re
from datetime import datetime

# Third Party
from pytz import timezone
from dateutil.parser import parse

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
        raise InvalidUsage('Invalid header provided')


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
    if not isinstance(str_datetime, basestring):
        raise InvalidUsage('datetime should be provided in str format as 2015-10-08T06:16:55Z')
    utc_pattern = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
    if re.match(utc_pattern, str_datetime):
        return True
    else:
        raise InvalidUsage('Invalid DateTime: Kindly specify UTC datetime in ISO-8601 format '
                           'like 2015-10-08T06:16:55Z. Given Date is %s' % str_datetime)


def is_future_datetime(dt):
    """
    This function validates that given datetime obj has date and time in future by comparing
    with current UTC datetime object.
    :param dt: datetime obj
    :type dt: datetime
    :exception: Invalid usage
    :return: True if given datetime is ahead of current datetime
    :rtype: bool
    """
    if not isinstance(dt, datetime):
        raise InvalidUsage('param should be a datetime object')
    return dt > datetime.utcnow().replace(tzinfo=timezone('UTC'))


def validate_format_and_future_datetime(datetime_str):
    """
    Here we check given string datetime is in valid format, then we convert it into datetime obj.
    Finally we check if it is in future.
    This uses validate_format_and_get_utc_datetime_from_str() and is_future_datetime() functions.
    :param datetime_str:
    :type datetime_str: str
    :return:
    """
    if not is_future_datetime(validate_format_and_get_utc_datetime_from_str(datetime_str)):
        raise InvalidUsage("Given datetime(%s) should be in future" % datetime_str)


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


def validate_format_and_get_utc_datetime_from_str(str_datetime):
    """
    This converts given string datetime into UTC datetime obj.
    This uses validate_datetime_format() to validate the format of given str.
    Valid format should be like 2015-10-08T06:16:55Z
    :param str_datetime:
    :return: datetime obj
    :rtype: datetime
    """
    if not isinstance(str_datetime, basestring):
        raise InvalidUsage('param should be a string of datetime')
    validate_datetime_format(str_datetime)
    return parse(str_datetime).replace(tzinfo=timezone('UTC'))
