"""
This file contains handy functions related to datetime objects encapsulated under class
DatetimeUtils.
"""
# Standard Imports
from datetime import datetime, timedelta

# Third Party
import pytz
from pytz import timezone
from dateutil import parser
from dateutil.tz import tzutc
from dateutil.parser import parse

# Application Specific
from ..error_handling import InvalidUsage
from validators import raise_if_not_instance_of


class DatetimeUtils(object):
    """
    This class contains handy functions to deal with datetime objects
    """
    ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, value):
        self.value = value

    @staticmethod
    def validate_datetime_in_iso_utc_format(str_datetime):
        """
        This validates the given datetime is in ISO UTC format or not. Proper format should be like
        '2015-10-08T06:16:55.000Z'.

        :param str_datetime: str
        :type str_datetime: str
        :exception: Invalid Usage
        :return: True if given datetime is valid, raises Invalid usage otherwise.
        :rtype: bool | InvalidUsage
        """
        if not isinstance(str_datetime, basestring):
            raise InvalidUsage('datetime should be provided in str format '
                               'as 2015-10-08T06:16:00.000Z')
        try:
            datetime.strptime(str_datetime, DatetimeUtils.ISO8601_FORMAT)
        except ValueError:
            raise InvalidUsage('Invalid DateTime: Kindly specify UTC datetime in ISO-8601 format '
                               'like 2015-10-08T06:16:00.000Z. Given Date is %s' % str_datetime)
        return True

    def is_in_future(self, neg_offset=0, pos_offset=0):
        """
        This function validates that calling datetime object has date and time in future by
        comparing with current UTC datetime object.
        Datetime value of calling object must have timezone information in it.
        :param neg_offset: number of seconds to be subtracted from current datetime
        :param pos_offset: number of seconds to be added from current datetime
        :type neg_offset; int | long | float
        :type pos_offset; int | long | float
        :exception: Invalid usage
        :return: True if given datetime is ahead of current datetime
        :rtype: bool

        **Usage**
            To use this method
                >>> obj = DatetimeUtils(datetime.utcnow() + timedelta(minutes=2))
                >>> obj.is_in_future()
                >>> True
        """
        raise_if_not_instance_of(neg_offset, (int, long, float))
        raise_if_not_instance_of(pos_offset, (int, long, float))
        current_datetime = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(seconds=neg_offset) + timedelta(seconds=pos_offset)
        return self.value > current_datetime

    @classmethod
    def get_datetime_obj_if_str_datetime_is_in_valid_iso_format(cls, str_datetime):
        """
        This converts given string datetime into UTC datetime obj.
        This uses validate_datetime_in_iso_utc_format() to validate the format of given str.
        Valid format should be like 2015-10-08T06:16:55Z
        :param str_datetime:
        :return: datetime obj
        :rtype: datetime
        """
        if not isinstance(str_datetime, basestring):
            raise InvalidUsage('param should be a string of datetime')
        cls.validate_datetime_in_iso_utc_format(str_datetime)
        return parse(str_datetime).replace(tzinfo=tzutc())

    @staticmethod
    def to_utc_str(datetime_obj):
        """
        This converts given datetime in '2015-10-08T06:16:55.000Z' format.
        :param datetime_obj: given datetime object
        :type datetime_obj: datetime
        :return: UTC date in str
        :rtype: str
        """
        if not isinstance(datetime_obj, datetime):
            raise InvalidUsage('Given param should be datetime obj')
        return datetime_obj.strftime(DatetimeUtils.ISO8601_FORMAT)

    @staticmethod
    def utc_isoformat(datetime_obj):
        """
        :param datetime.datetime datetime_obj: Datetime object
        :return: Datetime object in ISO-8601 format (UTC)
        :rtype: str
        """
        return datetime_obj.replace(tzinfo=pytz.utc).isoformat()

    @staticmethod
    def isoformat_to_mysql_datetime(iso8601_datetime_string):
        """
        Function converts ISO 8601 datetime string to MySQL acceptable datetime string
        Example:
            >>> iso8061_datetime_string = "2016-03-02T08:44:55+00:00"
            >>> return "2016-03-02 08:44:55"
        :type iso8601_datetime_string:  str
        :param iso8601_datetime_string:  "2016-03-02T08:44:55+00:00"
        :rtype: str
        """
        datetime_object = parser.parse(iso8601_datetime_string)
        return datetime_object.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def isoformat_to_datetime(iso8601_datetime_string):
        """
        :param str iso8601_datetime_string: ISO8601 formatted datetime string
        :rtype: datetime
        """
        return datetime.strptime(iso8601_datetime_string, DatetimeUtils.ISO8601_FORMAT)

    @staticmethod
    def unix_time(datetime_obj):
        """
        Converts datetime_obj(UTC) datetime object to epoch in seconds
        :param datetime_obj:
        :type datetime_obj: datetime
        :return: returns epoch time in milliseconds.
        :rtype: long
        """
        epoch = datetime(1970, 1, 1, tzinfo=tzutc())
        delta = datetime_obj - epoch
        return delta.total_seconds()

    @staticmethod
    def get_utc_datetime(datetime_obj, given_timezone):
        """
        This method takes datetime object and timezone name and returns UTC specific datetime string
        :Example:
            >> now = datetime.now()  # datetime(2015, 10, 8, 11, 16, 55, 520914)
            >> timezone = 'Asia/Karachi'
            >> utc_datetime = get_utc_datetime(now, timezone) # '2015-10-08T06:16:55Z
        :param datetime_obj: datetime object
        :param given_timezone: timezone
        :type datetime_obj: datetime
        :type given_timezone: str
        :return: timezone specific datetime object
        :rtype string
        """
        raise_if_not_instance_of(given_timezone, basestring)
        raise_if_not_instance_of(datetime_obj, datetime)
        # get timezone info from given datetime object
        local_timezone = timezone(given_timezone)
        try:
            local_dt = local_timezone.localize(datetime_obj, is_dst=None)
        except ValueError:
            # datetime object already contains timezone info
            return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
