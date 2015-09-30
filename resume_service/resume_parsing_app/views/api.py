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

# Application specific/third party libs
from .app_constants import Constants as current
from .parse_lib import parse_resume
from .utils import create_candidate_from_parsed_resume
from boto.s3.connection import S3Connection
import requests

mod = Blueprint('activities_api', __name__)


@mod.route('/')
def hello_world():
    return '/parse_resume'


@mod.route('/parse_resume', methods=['POST'])
def parse_file_picker_resume():
    """Parses resume uploaded on S3

    Returns:
        result_dict: a json string extrapolating the processed resume.
    """
    # Ensure we were passed a valid token by passing it to our AuthServer.
    try:
        oauth_token = request.headers['Authorization']
    except KeyError:
        return jsonify({'error': {'message': 'No Auth header set'}}), 400
    r = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
    if r.status_code != 200:
        return jsonify({'error': {'message': 'Invalid Authorization'}}), 401
    valid_user_id = json.loads(r.text).get('user_id')
    if not valid_user_id:
        return jsonify({'error': {'message': 'Oauth did not provide a valid user_id'}}), 400
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

    result_dict = parse_resume(file_obj=resume_file, filename_str=filename_str)
    processed_data = result_dict.get('processed_data')
    if processed_data:
        del result_dict['processed_data']
    email_present = True if result_dict.get('emails') else False
    if create_candidate:
        if email_present:
            candidate_response = create_candidate_from_parsed_resume(result_dict, oauth_token)
            result_dict['id'] = candidate_response.get('candidates')[0]['id']
        else:
            return jsonify(**{'error': {'code': 3, 'message': 'Parsed resume did not have email',
                                        'candidate': result_dict}}), 400

    return jsonify(**{'candidate': result_dict, 'dice_api_response': result_dict['dice_api_response']})