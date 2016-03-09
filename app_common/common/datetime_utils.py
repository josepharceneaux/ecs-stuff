import pytz
import datetime


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
