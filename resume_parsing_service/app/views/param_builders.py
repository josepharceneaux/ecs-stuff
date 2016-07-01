"""Code for building params dict from multiple types of requests objects."""
__author__ = 'erik@gettalent.com'
# pylint: disable=wrong-import-position, fixme, import-error
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InvalidUsage


def build_params_from_json(request):
    """
    Takes in flask request object with content-type of 'application/json' and returns params used
    in resume processing functions.
    :param flask.request:
    :return: dict
    """
    request_json = request.get_json()
    logger.info('Beginning parsing with JSON params: {}'.format(request_json))

    filepicker_key = request_json.get('filepicker_key')
    if not filepicker_key:
        raise InvalidUsage('Invalid JSON data for resume parsing')

    talent_pool_ids = request_json.get('talent_pool_ids')
    if not isinstance(talent_pool_ids, (list, type(None))):
        raise InvalidUsage('Invalid type for `talent_pool_ids`')

    resume_file_name = request_json.get('resume_file_name', filepicker_key)

    create_candidate = request_json.get('create_candidate', False)
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
