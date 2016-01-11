"""
This file contains validator methods which get arg specified key from dict and if key is not there,
  then throw exception of InvalidUsage
"""

# Third Party imports
from pytz import timezone
from dateutil.parser import parse

# App specific imports
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.common.utils.validators import is_valid_url

__author__ = 'saad'


def get_valid_data_from_dict(data, key):
    """
    Methods to Check if key exist and returns associated value
    :param data: json data with keyvalue pair
    :param key: key to check if missing or invalid value
    :return: value of associated key
    """
    assert isinstance(data, dict)
    try:
        value = data[key]
    except KeyError:
        raise InvalidUsage(error_message="Missing key: %s" % key)
    return value


def get_valid_datetime_from_dict(data, key):
    """
    Check if datetime is valid, if no, then raise invalid value exception
    """
    assert isinstance(data, dict)
    value = get_valid_data_from_dict(data, key)
    try:
        value = parse(value).replace(tzinfo=timezone('UTC'))
    except Exception:
        raise InvalidUsage(
            error_message="Invalid value of %s %s. %s should be in datetime format" % (key, value, key))
    return value


def get_valid_integer_from_dict(data, key):
    """
    Check if integer is valid, if no, then raise invalid value exception
    """
    assert isinstance(data, dict)
    value = get_valid_data_from_dict(data, key)
    if not str(value).isdigit():
        raise InvalidUsage(error_message='Invalid value of %s. It should be integer' % key)
    return value


def get_valid_url_from_dict(data, key):
    """
    Check if url is valid, if no, then raise invalid value exception
    """
    assert isinstance(data, dict)
    value = get_valid_data_from_dict(data, key)
    if not is_valid_url(value):
        raise InvalidUsage(error_message='Invalid value of %s.' % key)
    return value
