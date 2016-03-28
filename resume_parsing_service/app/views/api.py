"""API for the Resume Parsing App"""
# pylint: disable=wrong-import-position, fixme
__author__ = 'erikfarmer'
# Framework specific
from flask import Blueprint
from flask import request
from flask import jsonify
from flask.ext.cors import CORS
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InvalidUsage
from resume_parsing_service.app.views.batch_lib import process_batch_item
from resume_parsing_service.app.views.batch_lib import add_fp_keys_to_queue
from resume_parsing_service.app.views.parse_lib import process_resume
from resume_parsing_service.app.views.utils import get_users_talent_pools
from resume_parsing_service.common.utils.auth_utils import require_oauth
from resume_parsing_service.common.routes import ResumeApi

PARSE_MOD = Blueprint('resume_api', __name__)

# Enable CORS
CORS(PARSE_MOD, resources={
    r'/v1/{}'.format(ResumeApi.PARSE): {
        'origins': [r"*.gettalent.com", "http://localhost"],
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
    oauth = request.oauth_token
    content_type = request.headers.get('content-type')
    # Handle posted JSON data from web app/future clients. This block should consume filepicker
    # key and filename.
    if 'application/json' in content_type:
        request_json = request.get_json()
        create_candidate = request_json.get('create_candidate', False)
        talent_pool_ids = request_json.get('talent_pool_ids')
        if not isinstance(talent_pool_ids, (list, type(None))):
            raise InvalidUsage('Invalid type for `talent_pool_ids`')
        filepicker_key = request_json.get('filepicker_key')
        resume_file = None
        resume_file_name = str(filepicker_key)
        if not filepicker_key:
            raise InvalidUsage('Invalid JSON data for resume parsing')
    # Handle posted form data. Required for mobile app as it posts a binary file
    elif 'multipart/form-data' in content_type:
        # create_candidate is passed as a string from a form so this extra processing is needed.
        create_mode = request.form.get('create_candidate', 'false')
        create_candidate = True if create_mode.lower() == 'true' else False
        filepicker_key = None
        resume_file = request.files.get('resume_file')
        resume_file_name = request.form.get('resume_file_name')
        talent_pool_ids = None
        if not (resume_file and resume_file_name):
            raise InvalidUsage('Invalid form data for resume parsing.')
    else:
        logger.debug("Invalid Header set. Form: {}. Files: {}. JSON: {}".format(
            request.form, request.files, request.json
        ))
        raise InvalidUsage("Invalid Request. Bad Headers set.")
    # If the array is passed set it, else retrieve the first ID given by candidate_pool_service
    if talent_pool_ids:
        talent_pools = talent_pool_ids
    else:
        talent_pools = get_users_talent_pools(oauth)
    if not isinstance(create_candidate, bool):
        raise InvalidUsage('Invalid parameter for create_candidate.')
    if create_candidate and not talent_pools:
        raise InvalidUsage("Could not obtain user talent_pools for candidate creation.")
    parse_params = {
        'oauth': oauth,
        'talent_pools': talent_pools,
        'create_candidate': create_candidate,
        'filename': resume_file_name,
        'filepicker_key': filepicker_key,
        'resume_file': resume_file
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
    parsing_response = process_batch_item(user_id)
    return jsonify(**parsing_response), 200
