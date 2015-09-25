from StringIO import StringIO
import json
import urllib2

from flask import Flask, request
from flask import jsonify
from boto.s3.connection import S3Connection

from resume_parser.app_constants import Constants as current
from resume_parser.parse_lib import parse_resume
from utils import create_candidate_from_parsed_resume

app = Flask(__name__)
app.config.from_object('config')


@app.route('/')
def hello_world():
    return '/parse_resume'


@app.route('/parse_resume', methods=['POST'])
def parse_file_picker_resume():
    """Parses resume uploaded on S3

    Returns:
        result_dict: a json string extrapolating the processed resume.
    """
    # Ensure we were passed a valid token by passing it to our AuthServer.
    try:
        oauth_token = request.headers['Authorization']
    except KeyError:
        return jsonify({'error': 'Invalid query params'}), 400
    req = urllib2.Request(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        return jsonify({'error': 'Invalid query params'}), 400
    page = response.read()
    json_response = json.loads(page)
    if not json_response.get('user_id'):
        return jsonify({'error': 'Invalid query params'}), 400
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
    email_present = True if result_dict.get('emails') else False
    if create_candidate:
        if email_present:
            candidate_response = create_candidate_from_parsed_resume(result_dict, oauth_token)
            result_dict['id'] = candidate_response.get('candidates')[0]['id']
        else:
            return jsonify(**{'error': {'code': 3, 'message': 'Parsed resume did not have email',
                                        'candidate': result_dict}}), 400


    return jsonify(**{'candidate':result_dict})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
