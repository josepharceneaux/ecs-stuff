"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have validators for campaign services.
"""

# Standard Imports
import re
from datetime import datetime, timedelta
from werkzeug.exceptions import BadRequest

# Third Party
from pytz import timezone
from dateutil.parser import parse

# Common utils
from ..error_handling import InvalidUsage
from campaign_utils import frequency_id_to_seconds
from ..utils.handy_functions import JSON_CONTENT_TYPE_HEADER


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


def is_datetime_in_future(dt):
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


def is_datetime_in_valid_format_and_in_future(datetime_str):
    """
    Here we check given string datetime is in valid format, then we convert it into datetime obj.
    Finally we check if it is in future.
    This uses if_str_datetime_in_valid_format_get_datetime_obj() and is_datetime_in_future() functions.
    :param datetime_str:
    :type datetime_str: str
    :return:
    """
    if not is_datetime_in_future(if_str_datetime_in_valid_format_get_datetime_obj(datetime_str)):
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


def if_str_datetime_in_valid_format_get_datetime_obj(str_datetime):
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


def validation_of_data_to_schedule_campaign(campaign_obj, request):
    """
    This validates the data provided to schedule a campaign.
    1- Get JSON data from request and raise Invalid Usage exception if no data is found or
            data is not JSON serializable.
    2- If start datetime is not provide/given in invalid format/is in past, we raise Invalid usage
        error as start_datetime is required field for both 'periodic' and 'one_time' schedule.
    3- Get number of seconds by validating given frequency_id
    4- If end_datetime and frequency, both are provided then we validate same checks for
        end_datetime as we did in step 2 for start_datetime.
    5- Removes the frequency_id from given dict of data and put frequency (number of seconds) in it.
    6- Returns data_to_schedule

    This function is used in pre_process_schedule() of CampaignBase class.

    :param campaign_obj: campaign obj
    :param request: request received on API
    :return: data_to_schedule
    :rtype: dict
    """
    try:
        data_to_schedule_campaign = request.get_json()
    except BadRequest:
        raise InvalidUsage('Given data is not JSON serializable.')
    if not data_to_schedule_campaign:
        raise InvalidUsage('No data provided to schedule %s (id:%s)'
                           % (campaign_obj.__tablename__, campaign_obj.id))
    # check if data has start_datetime
    if not data_to_schedule_campaign.get('start_datetime'):
        raise InvalidUsage('start_datetime is required field.')
    # start datetime should be in valid format and in future
    is_datetime_in_valid_format_and_in_future(data_to_schedule_campaign.get('start_datetime'))
    # get start_datetime object
    start_datetime = if_str_datetime_in_valid_format_get_datetime_obj(
        data_to_schedule_campaign.get('start_datetime'))
    end_datetime_str = data_to_schedule_campaign.get('end_datetime')
    # get number of seconds from frequency id
    frequency = frequency_id_to_seconds(data_to_schedule_campaign.get('frequency_id'))
    # check if task to be schedule is periodic
    if end_datetime_str and frequency:
        # check if end_datetime is greater than start_datetime
        end_datetime_plus_frequency = \
            if_str_datetime_in_valid_format_get_datetime_obj(end_datetime_str)\
            + timedelta(seconds=frequency)
        if end_datetime_plus_frequency < start_datetime:
            raise InvalidUsage("end_datetime must be greater than start_datetime")
    data_to_schedule_campaign['frequency'] = frequency
    return data_to_schedule_campaign
