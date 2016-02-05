"""API for the Resume Parsing App"""
__author__ = 'erikfarmer'
# Framework specific
from flask import Blueprint
from flask import request
from flask import jsonify
from flask.ext.cors import CORS
# Module Specific
from resume_parsing_service.common.error_handling import InvalidUsage
from resume_parsing_service.app.views.batch_lib import _process_batch_item
from resume_parsing_service.app.views.batch_lib import add_fp_keys_to_queue
from resume_parsing_service.app.views.parse_lib import process_resume
from resume_parsing_service.app.views.utils import get_users_talent_pools
from resume_parsing_service.common.utils.auth_utils import require_oauth
from resume_parsing_service.common.routes import ResumeApi


PARSE_MOD = Blueprint('resume_api', __name__)


# Enable CORS
CORS(PARSE_MOD, resources={
    r'/v1/{}'.format(ResumeApi.PARSE): {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@PARSE_MOD.route('/')
def index():
    """Uptime/version checkable URL"""
    return '/' + ResumeApi.PARSE


@PARSE_MOD.route(ResumeApi.PARSE, methods=['POST'])
@require_oauth()
def resume_post_reciever():
    """
    Builds a kwargs dict for used in abstracted process_resume.
    :return: dict: {'candidate': {}}
    """
    # Get the resume file object from Filepicker or the request body, if provided
    request_json = request.get_json() or {}
    filepicker_key = request.form.get('filepicker_key') or request_json.get('filepicker_key')
    resume_file_name = request.form.get('resume_file_name') or request_json.get('resume_file_name')
    create_candidate = request.form.get('create_candidate') or request_json.get('create_candidate')
    oauth = request.oauth_token
    talent_pools = get_users_talent_pools(oauth)
    if filepicker_key:
        resume_file = None
        resume_file_name = str(filepicker_key)
    elif resume_file_name:
        if request_json:
            raise InvalidUsage("Posted Resumes must be sent as forms (multipart/form-data)")
        resume_file = request.files['resume_file']
    else:
        raise InvalidUsage("Invalid Query Params")
    parse_params = {
        'filepicker_key': filepicker_key,
        'resume_file': resume_file,
        'filename': resume_file_name,
        'create_candidate': create_candidate,
        'oauth': oauth,
        'talent_pools': talent_pools
    }
    return jsonify(**process_resume(parse_params))


@PARSE_MOD.route(ResumeApi.BATCH, methods=['POST'])
@require_oauth()
def post_files_to_queue():
    """
    Endpoint for posting files in format {'filenames': ['file1', 'file2, ...]
    :return: Error/Success Response.
    """
    user_id = request.user.id
    # oauth_token is in format "bearer foo".
    oauth = request.oauth_token
    request_json = request.get_json()
    if not request_json:
        raise InvalidUsage("Request headers have invalid content-type")
    filepicker_keys = request_json.get('filenames')
    if filepicker_keys:
        queue_details = add_fp_keys_to_queue(filepicker_keys, user_id, oauth)
        return jsonify(**queue_details), 201
    else:
        raise InvalidUsage("No filenames provided to /batch")


@PARSE_MOD.route('batch/<int:user_id>', methods=['GET'])
@require_oauth()
def process_batch_request(user_id):
    """
    End Point for getting the processed candidate object representing the first item in a users
    resume processing queue.
    :param int user_id: The user who 'owns' the queue.
    :return: HTTP/JSON response containing parsed resume information.
    """
    # TODO: add in TalentPool capturing.
    parsing_response = _process_batch_item(user_id)
    return jsonify(**parsing_response), 200
