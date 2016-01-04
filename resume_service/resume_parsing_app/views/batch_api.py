"""Api endpoints used to establish batch resume parsing processes."""
__author__ = 'erik@getTalent'
# Framework specific.
from flask import Blueprint
from flask import request
from flask import jsonify
# Module specific.
from resume_service.common.utils.auth_utils import require_oauth
from resume_service.common.redis_conn import redis_client
from resume_service.resume_parsing_app.views.batch_lib import add_fp_keys_to_queue
from resume_service.resume_parsing_app.views.api import _parse_file_picker_resume

BATCH_MOD = Blueprint('batch_processing', __name__)


@BATCH_MOD.route('/', methods=['POST'])
@require_oauth
def post_files_to_queue():
    """
    Endpoint for posting files in format {'filenames': ['file1', 'file2, ...]
    :return: Error/Success Response.
    """
    user_id = request.user.id
    request_json = request.get_json()
    filepicker_keys = request_json.get('filenames')
    if filepicker_keys:
        queue_details = add_fp_keys_to_queue(filepicker_keys, user_id)
        return queue_details, 201
    else:
        return jsonify(**{'error': {'message': 'No filenames provided'}}), 400


@BATCH_MOD.route('/process/<int:user_id>', methods=['POST'])
@require_oauth
def process_batch_item(user_id, create_candidate=True, oauth=None):
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    fp_key = redis_client.lpop(queue_string)
    # we need to get the token from the db
    # LPOP returns none if the list is empty so we should end our current batch.
    if fp_key is None:
        return jsonify(**{'error': {'message': 'Invalid FP Key provided'}})
    else:
        parse_params = {
            'filepicker_key': fp_key,
            'create_candidate': create_candidate,
            'oauth': oauth
        }
        return jsonify(**_parse_file_picker_resume(parse_params))