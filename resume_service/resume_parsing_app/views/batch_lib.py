"""Functions used by batch processing endpoints."""
__author__ = 'erik@getTalent'
# Module Specific
from resume_service.common.redis_conn import redis_client


def add_fp_keys_to_queue(filepicker_keys, user_id):
    """
    Adds filename to redis list. The redis key is formed using the user_id.
    :param list filepicker_keys:
    :param str user_id:
    :return str:
    """
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    list_length = redis_client.rpush(queue_string, *filepicker_keys)
    return {'redis_key': queue_string, 'quantity': list_length}
