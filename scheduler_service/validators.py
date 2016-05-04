"""
This file contains validator methods which get arg specified key from dict and if key is not there,
  then throw exception of InvalidUsage
"""

# Third Party imports
from pytz import timezone
from dateutil.parser import parse

# App specific imports
from scheduler_service import SchedulerUtils
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.common.utils.validators import is_valid_url_format

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


def get_valid_task_name_from_dict(data, key):
    """
    Check if the task_name value has alphanumeric, unique and allowed characters.
    Also `run_job` shouldn't be the task_name as its a default callback for every user based task
    :param data: dictionary consisting of acpscheduler tasks
    :type data: dict
    :param key: key to get from data dictionary
    :type key: str
    """
    assert isinstance(data, dict)
    value = str(get_valid_data_from_dict(data, key))
    general_msg = "Invalid value of %s %s. %s should be unique, alphanumeric and allowed characters are [-, _ ]. " \
                  "Note: `%s` is not allowed as a task name." % (key, value, key, SchedulerUtils.RUN_JOB_METHOD_NAME)
    if value.lower() == SchedulerUtils.RUN_JOB_METHOD_NAME.lower():
        raise InvalidUsage(error_message=general_msg)

    allowed_characters = ['-', '_']
    if any(c for c in value if not(c.isalnum() or c in allowed_characters)):
        raise InvalidUsage(error_message=general_msg)

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
    if not is_valid_url_format(value):
        raise InvalidUsage(error_message='Invalid value of %s.' % key)
    return value
