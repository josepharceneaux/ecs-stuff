"""
Functions to be used in v1 banner endpoints
"""
__author__ = 'erik@getTalent'
# StdLib
from time import time
# Third Party
from flask import jsonify, request
# Module Specific
from banner_service.app import redis_store
from banner_service.common.error_handling import InvalidUsage

BANNER_REDIS_KEY = 'gt_global_banner'
REQUIRED_DATA = ('title', 'text', 'link', 'color')


def create_banner(json_data):
    # Check to see if there is an existing entry at the key prefix
    existing_banner = redis_store.hgetall(BANNER_REDIS_KEY)
    # Return Error if so
    if existing_banner:
        raise InvalidUsage(
            error_message="Cannot POST banner when an active banner exists")

    for required_param in REQUIRED_DATA:
        if not json_data.get(required_param):
            raise InvalidUsage(
                error_message='Missing param: {}'.format(required_param))

    json_data['timestamp'] = time()
    # TODO Implement validated user ID
    # posted_data['owner_id'] = request.user.id

    return redis_store.hmset(BANNER_REDIS_KEY, json_data)


def read_banner():
    existing_banner = redis_store.hgetall(BANNER_REDIS_KEY)
    if not existing_banner:
        raise InvalidUsage(error_message='No banner currently set.')

    return existing_banner


def delete_banner():
    existing_banner = redis_store.hgetall(BANNER_REDIS_KEY)
    if not existing_banner:
        raise InvalidUsage(error_message='No banner currently set.')

    return redis_store.delete(BANNER_REDIS_KEY) == 1
