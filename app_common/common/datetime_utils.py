# Standard Imports
from datetime import datetime

# Third Party
import pytz
from dateutil import parser
from dateutil.tz import tzutc
from flask import current_app
from dateutil.parser import parse

# Application Specific
from pytz import timezone
from error_handling import InvalidUsage
from talent_config_manager import TalentConfigKeys


class DatetimeUtils(object):
    """
    This class contains handy functions to deal with datetime objects
    """
    ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    @classmethod
    def validate_datetime_format(cls, str_datetime):
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
            datetime.strptime(str_datetime, cls.ISO8601_FORMAT)
        except ValueError:
            raise InvalidUsage('Invalid DateTime: Kindly specify UTC datetime in ISO-8601 format '
                               'like 2015-10-08T06:16:00.000Z. Given Date is %s' % str_datetime)
        return True

    @staticmethod
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
        return dt > datetime.utcnow().replace(tzinfo=tzutc())

    @classmethod
    def is_datetime_in_valid_format_and_in_future(cls, datetime_str):
        """
        Here we check given string datetime is in valid format, then we convert it
        into datetime obj. Finally we check if it is in future.
        This uses get_datetime_obj_if_str_datetime_in_valid_format()
        and is_datetime_in_future() functions.
        :param datetime_str:
        :type datetime_str: str
        """
        logger = current_app.config[TalentConfigKeys.LOGGER]
        if not cls.is_datetime_in_future(cls.get_datetime_obj_if_str_datetime_in_valid_format(datetime_str)):
            logger.error('Datetime str should be in future. %s' % datetime_str)
            raise InvalidUsage("Given datetime(%s) should be in future" % datetime_str)

    @classmethod
    def get_datetime_obj_if_str_datetime_in_valid_format(cls, str_datetime):
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
        cls.validate_datetime_format(str_datetime)
        return parse(str_datetime).replace(tzinfo=tzutc())

    @classmethod
    def to_utc_str(cls, datetime_obj):
        """
        This converts given datetime in '2015-10-08T06:16:55.000Z' format.
        :param datetime_obj: given datetime object
        :type datetime_obj: datetime
        :return: UTC date in str
        :rtype: str
        """
        if not isinstance(datetime_obj, datetime):
            raise InvalidUsage('Given param should be datetime obj')
        return datetime_obj.strftime(cls.ISO8601_FORMAT)

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
    def unix_time(dt):
        """
        Converts dt(UTC) datetime object to epoch in seconds
        :param dt:
        :type dt: datetime
        :return: returns epoch time in milliseconds.
        :rtype: long
        """
        epoch = datetime(1970, 1, 1, tzinfo=tzutc())
        delta = dt - epoch
        return delta.total_seconds()

    @staticmethod
    def get_utc_datetime(dt, tz):
        """
        This method takes datetime object and timezone name and returns UTC specific datetime
        :Example:
            >> now = datetime.now()  # datetime(2015, 10, 8, 11, 16, 55, 520914)
            >> timezone = 'Asia/Karachi'
            >> utc_datetime = get_utc_datetime(now, timezone) # '2015-10-08T06:16:55Z
        :param dt: datetime object
        :type dt: datetime
        :return: timezone specific datetime object
        :rtype string
        """
        assert tz, 'Timezone should not be none'
        assert isinstance(dt, datetime), 'dt should be datetime object'
        # get timezone info from given datetime object
        local_timezone = timezone(tz)
        try:
            local_dt = local_timezone.localize(dt, is_dst=None)
        except ValueError:
            # datetime object already contains timezone info
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
