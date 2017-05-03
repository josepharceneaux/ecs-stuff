from datetime import datetime
import json
import re

from activity_service.app.constants.activity_messaging import MESSAGES
from activity_service.app import logger

EPOCH = datetime(year=1970, month=1, day=1)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


def get_recent_readable(activities, user_name):
    return {
        'total_count':
        activities.total,
        'items': [{
            'added_time': str(activity.added_time),
            'readable_text': activity_text(activity, user_name)
        } for activity in activities.items]
    }


def activity_text(activity, user_name):
    params = json.loads(activity.params) if activity.params else dict()
    # See GET-1946. JSON loads is returning unicode objects for some entries stored in DB.
    if isinstance(params, unicode):
        params = json.loads(params)

    params['username'] = user_name

    format_strings = MESSAGES.get(activity.type)
    if not format_strings:
        format_string = "No message for activity type {}".format(activity.type)
    else:  # one single activity
        format_string = format_strings['single']

    # If format_string has a param not in params, set it to unknown
    for param in re.findall(re.compile(r'%\((\w+)\)s'), format_string):
        if not params.get(param):
            params[param] = 'unknown'

    for k, v in params.iteritems():
        params[k] = v.encode('utf-8', 'replace')

    try:
        formatted_string = format_string.format(**params)
    except UnicodeEncodeError:
        logger.exception('V2UnicodeError: {}'.format(params))
        return None

    if 'You has' in formatted_string:
        # To fix 'You has joined'
        formatted_string = formatted_string.replace('You has', 'You have')
    elif "You's" in formatted_string:
        # To fix "You's recurring campaign has expired"
        formatted_string = formatted_string.replace("You's", "Your")

    return formatted_string
