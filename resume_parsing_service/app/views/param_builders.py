"""Code for building params dict from multiple types of requests objects."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position, fixme, import-error
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InvalidUsage
from resume_parsing_service.common.utils.validators import get_json_data_if_validated
from resume_parsing_service.json_schemas.resumes_post_schema import create_candidate_schema



def build_params_from_json(request):
    """
    Takes in flask request object with content-type of 'application/json' and returns params used
    in resume processing functions.
    :param flask.request request:
    :rtype: dict
    """
    custom_error = 'There has been a critical error parsing this resume, the development team has been notified'
    request_json = get_json_data_if_validated(request, create_candidate_schema, custom_msg=custom_error)
    logger.info('Beginning parsing with JSON params: {}'.format(request_json))

    filepicker_key = request_json['filepicker_key']
    create_candidate = request_json.get('create_candidate', False)
    resume_file_name = request_json.get('resume_file_name', filepicker_key)
    talent_pool_ids = request_json.get('talent_pool_ids')
    resume_file = None

    parse_params = {
        'create_candidate': create_candidate,
        'filename': resume_file_name,
        'filepicker_key': filepicker_key,
        'resume_file': resume_file,
        'talent_pools': talent_pool_ids
    }

    return parse_params


def build_params_from_form(request):
    """
    Takes in flask request object with content-type of 'multipart/form-data' and returns params
    used in resume processing functions.
    :param flask.request request:
    :return: dict
    """
    resume_file = request.files.get('resume_file')
    resume_file_name = request.form.get('resume_file_name')
    if not (resume_file and resume_file_name):
        raise InvalidUsage('Invalid form data for resume parsing.')

    # create_candidate is passed as a string from a form so this extra processing is needed.
    create_mode = request.form.get('create_candidate', 'false')
    create_candidate = True if create_mode.lower() == 'true' else False
    filepicker_key = None
    talent_pool_ids = None

    parse_params = {
        'create_candidate': create_candidate,
        'filename': resume_file_name,
        'filepicker_key': filepicker_key,
        'resume_file': resume_file,
        'talent_pools': talent_pool_ids
    }

    return parse_params
