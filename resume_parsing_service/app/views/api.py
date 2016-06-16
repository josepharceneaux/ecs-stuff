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
from resume_parsing_service.app.views.param_builders import build_params_from_form
from resume_parsing_service.app.views.param_builders import build_params_from_json
from resume_parsing_service.app.views.resume_processor import process_resume
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


@PARSE_MOD.route(ResumeApi.PARSE, methods=['POST'])
@require_oauth()
def resume_post_receiver():
    """
    Builds a kwargs dict for used in abstracted process_resume.
    :return: dict: {'candidate': {}}
    """
    oauth = request.oauth_token
    content_type = request.headers.get('content-type')

    # Handle posted JSON data from web app/future clients.
    # This block should consume filepicker key and filename.
    if 'application/json' in content_type:
        parse_params = build_params_from_json(request)
    # Handle posted form data. Required for mobile app as it posts a file.
    elif 'multipart/form-data' in content_type:
        parse_params = build_params_from_form(request)
    else:
        logger.debug("Invalid Header set. Form: {}. Files: {}. JSON: {}".format(
            request.form, request.files, request.json
        ))
        raise InvalidUsage("Invalid Request. Bad Headers set.")

    parse_params['oauth'] = oauth
    # If the value is not set retrieve the first ID given by candidate_pool_service.
    if not parse_params['talent_pools']:
        parse_params['talent_pools'] = get_users_talent_pools(oauth)

    return jsonify(**process_resume(parse_params))
