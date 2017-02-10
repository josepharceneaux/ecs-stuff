"""
Functions used in v1 user_banner endpoints.
"""
from banner_service.app import redis_store

USER_BANNER_PREFIX = 'USER_BANNER_{}'


def create_user_banner_entry(user_id):
    """
    :param user_id:
    :return: Boolean
    """
    return redis_store.set(USER_BANNER_PREFIX.format(user_id), True)


def retrieve_user_banner_entry(user_id):
    return True if redis_store.get(
        USER_BANNER_PREFIX.format(user_id)) == 'True' else False
