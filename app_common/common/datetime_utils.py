import pytz
import datetime
from dateutil import parser


def utc_isoformat(datetime_obj):
    """

    :param datetime.datetime datetime_obj: Datetime object
    :return: Datetime object in ISO-8601 format (UTC)
    :rtype: str
    """
    return datetime_obj.replace(tzinfo=pytz.utc).isoformat()


def isoformat_to_datetime(iso8601_datetime_string):
    """
    :param str iso8601_datetime_string: ISO8601 formatted datetime string
    :rtype: datetime.datetime
    """
    return datetime.datetime.strptime(iso8601_datetime_string, "%Y-%m-%dT%H:%M:%S.%fZ")


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
