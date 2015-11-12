"""API for the Resume Parsing App"""
__author__ = 'erikfarmer'

# Standard lib
from StringIO import StringIO
import json

# Framework specific
from flask import Blueprint
from flask import current_app as app
from flask import request
from flask import jsonify
from flask.ext.cors import CORS

# Application specific/third party libs
from .app_constants import Constants as current
from .parse_lib import parse_resume
from .utils import create_candidate_from_parsed_resume
from boto.s3.connection import S3Connection
from common.utils.auth_utils import require_oauth

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
    """Parses resume uploaded on S3

    Returns:
        result_dict: a json string extrapolating the processed resume.
    """

    # Get the resume file object from Filepicker or the request body, if provided
    filepicker_key = request.form.get('filepicker_key')
    create_candidate = request.form.get('create_candidate')
    if filepicker_key:
        conn = S3Connection(current.AWS_ACCESS_KEY_ID, current.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(current.FILEPICKER_BUCKET_NAME)
        key_obj = bucket.get_key(str(filepicker_key))
        resume_file = StringIO(key_obj.get_contents_as_string())
        filename_str = key_obj.name
    elif request.form.get('resume_file_name'):
        resume_file = request.files['resume_file']
        resume_file = StringIO(resume_file.read())
        filename_str = request.form['resume_file_name']
    else:
        return jsonify({'error': 'Invalid query params'}), 400

    # Parse resume
    result_dict = parse_resume(file_obj=resume_file, filename_str=filename_str)
    processed_data = result_dict.get('dice_api_response')
    if processed_data:
        del result_dict['dice_api_response']
    email_present = True if result_dict.get('emails') else False
    if create_candidate:
        if email_present:
            candidate_response = create_candidate_from_parsed_resume(result_dict, request.oauth_token)
            candidate_id = json.loads(candidate_response).get('candidates')
            result_dict['id'] = candidate_id[0]['id'] if candidate_id else None
        else:
            return jsonify(**{'error': {'code': 3, 'message': 'Parsed resume did not have email',
                                        'candidate': result_dict}}), 400

    return jsonify(**{'candidate': result_dict, 'dice_api_response': processed_data})
