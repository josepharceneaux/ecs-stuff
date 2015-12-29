"""Api endpoints used to establish batch resume parsing processes."""
__author__ = 'erik@getTalent'
# Framework specific.
from flask import Blueprint
from flask import request
from flask import jsonify
# Module specific.
from resume_service.common.utils.auth_utils import require_oauth
from resume_service.resume_parsing_app.views.batch_lib import add_file_names_to_queue

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
    filenames = request_json.get('filenames')
    if filenames:
        queue_with_size = add_file_names_to_queue(filenames, user_id)
        # Should we return the list of filenames here? Possibly thousands of names.
        # Possibly just queue details?
        return queue_with_size, 201
    else:
        return jsonify(**{'error': {'message': 'No filenames provided'}}), 400
