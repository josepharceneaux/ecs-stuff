"""
Author: Zohaib Ijaz, QC-Technologies,
        Lahore, Punjab, Pakistan <mzohaib.qc@gmail.com>
        Saad Abdullah, QC-Technologies,
        Lahore, Punjab, Pakistan <saadfast.qc@gmail.com>

This module contains constants that can be used in all services.
"""
SLEEP_TIME = 30
SLEEP_INTERVAL = 3

RETRY_ATTEMPTS = 10
REQUEST_TIMEOUT = 30
CANDIDATE_ALREADY_EXIST = 3013
REDIS2 = 'REDIS2'


"""
 Mock Service and other services common constants
"""
MEETUP = 'meetup'
EVENTBRITE = 'eventbrite'
FACEBOOK = 'facebook'
AUTH = 'auth'
API = 'api'


class HttpMethods(object):
    """
    Here we have names of HTTP methods
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'

# Custom Field Constants
INPUT = 'input'
PRE_DEFINED = 'pre-defined'
ALL = 'all'
CUSTOM_FIELD_TYPES = {INPUT: 'input', PRE_DEFINED: 'pre-defined'}
