import pytz


def utc_isoformat(datetime_obj):
    """

    :param datetime.datetime datetime_obj: Datetime object
    :return: Datetime object in ISO-8601 format (UTC)
    :rtype: str
    """
    return datetime_obj.replace(tzinfo=pytz.utc).isoformat()