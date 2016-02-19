"""Functions used by batch processing endpoints."""
# pylint: disable=wrong-import-position, fixme
__author__ = 'erik@getTalent'
# Standard Library
from datetime import datetime
from datetime import timedelta
import json
# Framework specific
from flask import jsonify
import requests
# Module Specific
from resume_parsing_service.app import redis_store
from resume_parsing_service.app.views.parse_lib import process_resume
from resume_parsing_service.app.views.utils import get_users_talent_pools
from resume_parsing_service.common.error_handling import TalentError
from resume_parsing_service.common.models.user import Token
from resume_parsing_service.common.routes import ResumeApiUrl, SchedulerApiUrl
from resume_parsing_service.common.utils.handy_functions import grouper


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def add_fp_keys_to_queue(filepicker_keys, user_id, token_str):
    """
    Adds filename to redis list. The redis key is formed using the user_id.
    :param list filepicker_keys:
    :param str user_id:
    :return str:
    """
    # Dirty hack for the time being. Need to go over API consistency after crunch period (1/28/16)
    if 'bearer' not in token_str:
        token_str = 'bearer {}'.format(token_str)
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    list_length = redis_store.rpush(queue_string, *filepicker_keys)
    batches = grouper(filepicker_keys, 100)
    scheduled = datetime.utcnow() + timedelta(seconds=15)
    for batch in batches:
        for file_name in batch:
            if not file_name:
                break
            payload = json.dumps({
                "task_type": "one_time",
                "run_datetime": scheduled.strftime(DATE_FORMAT),
                "url": "{}/{}".format(ResumeApiUrl.BATCH_URL, user_id),
            })
            scheduler_request = requests.post(SchedulerApiUrl.TASKS, data=payload,
                                              headers={
                                                  'Authorization': token_str,
                                                  'Content-Type': 'application/json'
                                              })
            if scheduler_request.status_code != 201:
                raise TalentError("Issue scheduling resume parsing {}".format(
                    scheduler_request.content))
        scheduled += timedelta(seconds=20)

    return {'redis_key': queue_string, 'quantity': list_length}


def _process_batch_item(user_id, create_candidate=True):
    """
    Endpoint for scheduler service to parse resumes update status data.
    :param int user_id: Id of the user who scheduled the batch process.
    :param bool create_candidate: Boolean for desire to create a candidate.
    :return: json dict in candidate object format.
    """
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    fp_key = redis_store.lpop(queue_string)
    # LPOP returns none if the list is empty so we should end our current batch.
    if fp_key is None:
        return jsonify(**{'error': {'message': 'Empty Queue for user: {}'.format(user_id)}})
    # Adding none here allows for unit-testing and will still result in unauthorized responses
    # given a user does not have a Token.
    oauth_token = Token.query.filter_by(user_id=user_id).first() or None
    formatted_token_header = "bearer {}".format(oauth_token.access_token)
    talent_pools = get_users_talent_pools(formatted_token_header)
    parse_params = {
        'talent_pools': talent_pools,
        'filepicker_key': fp_key,
        'create_candidate': create_candidate,
        'oauth': formatted_token_header
    }
    return process_resume(parse_params)
