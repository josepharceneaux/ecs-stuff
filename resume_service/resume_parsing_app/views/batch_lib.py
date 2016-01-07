"""Functions used by batch processing endpoints."""
__author__ = 'erik@getTalent'
# Framework specific
from flask import jsonify
# Module Specific
from resume_service.common.redis_conn import redis_client
from resume_service.common.models.user import Token
from resume_service.resume_parsing_app.views.parse_lib import _parse_file_picker_resume


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


def _process_batch_item(user_id, create_candidate=True):
    """
    Endpoint for scheduler service to parse resumes update status data.
    :param int user_id: Id of the user who scheduled the batch process.
    :param bool create_candidate: Boolean for desire to create a candidate.
    :return: json dict in candidate object format.
    """
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    fp_key = redis_client.lpop(queue_string)
    # LPOP returns none if the list is empty so we should end our current batch.
    if fp_key is None:
        return jsonify(**{'error': {'message': 'Empty Queue for user'.format(user_id)}})

    # Adding none here allows for unit-testing and will still result in unauthorized responses
    # given a user does not have a Token.
    oauth_token = Token.query.filter_by(user_id=user_id).first() or None
    parse_params = {
        'filepicker_key': fp_key,
        'create_candidate': create_candidate,
        'oauth': oauth_token
    }
    return _parse_file_picker_resume(parse_params)
