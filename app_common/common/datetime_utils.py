from datetime import tzinfo, timedelta


class SimpleUTC(tzinfo):
    """
    Python's datetime.utcnow() does not technically conform to ISO-8601 because it omits the timezone information
    at the end of the string.

    http://stackoverflow.com/questions/19654578/python-utc-datetime-objects-iso-format-dont-include-z-zulu-or-zero-offset
    """
    def tzname(self, date_time):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)


def utc_isoformat(datetime_obj):
    """

    :param datetime.datetime datetime_obj: Datetime object
    :return: Datetime object in ISO-8601 format (UTC)
    :rtype: str
    """
    return datetime_obj.replace(tzinfo=SimpleUTC()).isoformat()