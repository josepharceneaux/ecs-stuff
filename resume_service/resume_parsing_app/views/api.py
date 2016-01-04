"""API for the Resume Parsing App"""
__author__ = 'erikfarmer'
# Standard lib
from cStringIO import StringIO
import json
# Framework specific
from flask import Blueprint
from flask import request
from flask import jsonify
from flask.ext.cors import CORS
# Module Specific
from .parse_lib import parse_resume
from .utils import create_candidate_from_parsed_resume
from resume_service.common.utils.talent_s3 import download_file, get_s3_filepicker_bucket_and_conn
from resume_service.common.utils.auth_utils import require_oauth

mod = Blueprint('resume_api', __name__)


# Enable CORS
CORS(mod, resources={
    r'/parse_resume': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@mod.route('/')
def index():
    return '/parse_resume'


@mod.route('/parse_resume', methods=['POST'])
@require_oauth
def parse_file_picker_resume():
    """
    Builds a kwargs dict for used in abstracted _parse_file_picker_resume.
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
    return jsonify(**(_parse_file_picker_resume(parse_params)))


def _parse_file_picker_resume(parse_params):
    """
    Parses a resume based on a provided: filepicker key or binary, filename
    :return: dict: {'candidate': {}}
    """
    filepicker_key = parse_params.get('filepicker_key')
    create_candidate = parse_params.get('create_candidate')
    if filepicker_key:
        file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
        filename_str = filepicker_key
        resume_file = download_file(file_picker_bucket, filename_str)
    elif parse_params.get('filename'):
        resume_bin = parse_params.get('resume_file')
        resume_file = StringIO(resume_bin.read())
        filename_str = parse_params.get('filename')
    else:
        return {'error': 'Invalid query params'}, 400
    # Parse the actual resume content.
    result_dict = parse_resume(file_obj=resume_file, filename_str=filename_str)
    # Emails are the ONLY thing required to create a candidate.
    email_present = True if result_dict.get('emails') else False
    if create_candidate:
        if email_present:
            candidate_response = create_candidate_from_parsed_resume(result_dict,
                                                                     parse_params.get('oauth'))
            # TODO: add handling for candidate exists case.
            # Bad Response is:
            #             '{
            #   "error": {
            #     "message": "Candidate already exists, creation failed."
            #   }
            # }'
            candidate_id = json.loads(candidate_response).get('candidates')
            result_dict['id'] = candidate_id[0]['id'] if candidate_id else None
        else:
            return {'error': {'code': 3, 'message': 'Parsed resume did not have email',
                                        'candidate': result_dict}}, 400
    return {'candidate': result_dict}
