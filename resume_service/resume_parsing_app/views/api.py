"""API for the Resume Parsing App"""
__author__ = 'erikfarmer'
# Framework specific
from flask import Blueprint
from flask import request
from flask import jsonify
from flask.ext.cors import CORS
# Module Specific
from resume_service.common.utils.auth_utils import require_oauth
from resume_service.resume_parsing_app.views.parse_lib import process_resume
from resume_service.resume_parsing_app.views.batch_lib import add_fp_keys_to_queue
from resume_service.resume_parsing_app.views.batch_lib import _process_batch_item

PARSE_MOD = Blueprint('resume_api', __name__)


# Enable CORS
CORS(PARSE_MOD, resources={
    r'/parse_resume': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@PARSE_MOD.route('/')
def index():
    """Uptime checkable URL"""
    return '/parse_resume'


@PARSE_MOD.route('/parse_resume', methods=['POST'])
@require_oauth()
def resume_post_reciever():
    """
    Builds a kwargs dict for used in abstracted process_resume.
    :return: dict: {'candidate': {}}
    """
    # Get the resume file object from Filepicker or the request body, if provided
    filepicker_key = request.form.get('filepicker_key')
    create_candidate = request.form.get('create_candidate')
    oauth = request.oauth_token
    if filepicker_key:
        resume_file = None
        filename_str = str(filepicker_key)
    elif request.form.get('resume_file_name'):
        resume_file = request.files['resume_file']
        filename_str = request.form['resume_file_name']
    else:
        return jsonify({'error': 'Invalid query params'}), 400
    parse_params = {
        'filepicker_key': filepicker_key,
        'resume_file': resume_file,
        'filename': filename_str,
        'create_candidate': create_candidate,
        'oauth': oauth
    }
    return jsonify(**(process_resume(parse_params)))


@PARSE_MOD.route('/batch', methods=['POST'])
@require_oauth()
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


@PARSE_MOD.route('/batch/<int:user_id>', methods=['GET'])
@require_oauth()
def process_batch_item(user_id):
    """
    End Point for getting the processed candidate object representing the first item in a users
    resume processing queue.
    :param int user_id: The user who 'owns' the queue.
    :return: HTTP/JSON response containing parsed resume information.
    """
    parsing_response = _process_batch_item(user_id)
    return jsonify(**parsing_response), 200
