"""API for the Resume Parsing App"""

__author__ = 'erikfarmer'
# Standard lib
from cStringIO import StringIO
import json
# Framework specific
from flask import Blueprint
from flask import request
from flask import jsonify
# Module Specific
from .parse_lib import parse_resume
from .utils import create_candidate_from_parsed_resume
from resume_parsing_service.common.utils.talent_s3 import download_file, get_s3_filepicker_bucket_and_conn
from resume_parsing_service.common.utils.auth_utils import require_oauth
from resume_parsing_service.common.routes import ResumeApi

mod = Blueprint('resume_api', __name__)


@mod.route('/')
def index():
    return '/' + ResumeApi.PARSE


@mod.route(ResumeApi.PARSE, methods=['POST'])
@require_oauth()
def parse_file_picker_resume():
    """
    Parses a resume based on a provided: filepicker key or binary, filename
    :return: dict: {'candidate': {}}
    """
    # Get the resume file object from Filepicker or the request body, if provided
    filepicker_key = request.form.get('filepicker_key')
    create_candidate = request.form.get('create_candidate')
    if filepicker_key:
        file_picker_bucket, conn = get_s3_filepicker_bucket_and_conn()
        resume_file = download_file(file_picker_bucket, str(filepicker_key))
        filename_str = str(filepicker_key)
    elif request.form.get('resume_file_name'):
        resume_file = request.files['resume_file']
        resume_file = StringIO(resume_file.read())
        filename_str = request.form['resume_file_name']
    else:
        return jsonify({'error': 'Invalid query params'}), 400
    # Parse the actual resume content.
    result_dict = parse_resume(file_obj=resume_file, filename_str=filename_str)
    # Emails are the ONLY thing required to create a candidate.
    email_present = True if result_dict.get('emails') else False
    if create_candidate:
        if email_present:
            candidate_response = create_candidate_from_parsed_resume(result_dict,
                                                                     request.oauth_token)
            candidate_id = json.loads(candidate_response).get('candidates')
            result_dict['id'] = candidate_id[0]['id'] if candidate_id else None
        else:
            return jsonify(**{'error': {'code': 3, 'message': 'Parsed resume did not have email',
                                        'candidate': result_dict}}), 400

    return jsonify(**{'candidate': result_dict})
