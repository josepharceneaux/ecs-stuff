"""Main resume parsing logic & functions."""
# pylint: disable=wrong-import-position, fixme, import-error
__author__ = 'erik@gettalent.com'
# Standard library
import json
# Thid party
import requests
from contracts import contract
# Module specific
from flask import current_app
from resume_parsing_service.app import logger, redis_store
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.app.modules.decorators import upload_failed_IO
from resume_parsing_service.app.modules.optic_parse_lib import parse_optic_xml
from resume_parsing_service.app.modules.parse_lib import parse_resume
from resume_parsing_service.app.modules.utils import create_parsed_resume_candidate
from resume_parsing_service.app.modules.utils import gen_hash_from_file
from resume_parsing_service.app.modules.utils import resume_file_from_params
from resume_parsing_service.app.modules.utils import send_candidate_references
from resume_parsing_service.app.modules.utils import update_candidate_from_resume
from resume_parsing_service.common.error_handling import InvalidUsage
from resume_parsing_service.common.routes import CandidateApiUrl
from resume_parsing_service.common.utils.talent_s3 import boto3_put

IMAGE_FORMATS = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx',
                 '.pcx', '.jp2', '.jpc', '.jb2', '.djvu', '.djv']
DOC_FORMATS = ['.pdf', '.doc', '.docx', '.rtf', '.txt']
RESUME_EXPIRE_TIME = 60 * 60 * 24 * 7  # one week in seconds.


@contract
def process_resume(parse_params):
    """
    Parses a resume based on a provided: filepicker key or binary, filename
    :param dict parse_params:
    :return: Processed candidate data and BG info in form:
                {'candidate': {...}, 'raw': {...}}
    :rtype: dict
    """

    create_candidate = parse_params.get('create_candidate', False)

    # We need to obtain/define the file from our params.
    resume_file = resume_file_from_params(parse_params)
    filename_str = parse_params['filename']  # This is always set by param_builders.py

    # GET-2170 specifies caching of resumes only occurs in local/test environments.
    if current_app.config['GT_ENVIRONMENT'] in ('dev', 'jenkins'):
        cache_key_from_file = 'parsedResume_{}'.format(gen_hash_from_file(resume_file))
        cached_resume = get_cached_resume(resume_file, filename_str)
        if cached_resume:
            parsed_resume = cached_resume
        else:
            parsed_resume = parse_resume(resume_file, filename_str, cache_key_from_file)

    else:
        parsed_resume = parse_resume(resume_file, filename_str)

    if not create_candidate:
        return parsed_resume

    talent_pools = parse_params.get('talent_pool_ids')
    # Talent pools are the ONLY thing required to create a candidate.
    if create_candidate and not talent_pools:
        raise InvalidUsage(
            error_message=error_constants.NO_TP_ARG['message'],
            error_code=error_constants.NO_TP_ARG['code']
        )

    oauth_string = parse_params.get('oauth')
    parsed_resume['candidate']['talent_pool_ids']['add'] = talent_pools

    parsed_resume['candidate']['source_id'] = parse_params.get('source_id')
    parsed_resume['candidate']['source_product_id'] = parse_params.get('source_product_id')

    # Upload resumes we want to create candidates from.
    try:
        bucket = current_app.config['S3_BUCKET_NAME']
        boto3_put(resume_file.getvalue(), bucket, filename_str, 'OriginalFiles')
        parsed_resume['candidate']['resume_url'] = filename_str

    except Exception as e:
        logger.exception('Failure during s3 upload; reason: {}'.format(e.message))

    candidate_references = parsed_resume['candidate'].pop('references', None)
    candidate_created, candidate_id = create_parsed_resume_candidate(parsed_resume['candidate'],
                                                                     oauth_string)

    if not candidate_created:
        # We must update!
        parsed_resume['candidate']['id'] = candidate_id
        update_candidate_from_resume(parsed_resume['candidate'], oauth_string, filename_str)

    if candidate_references:
        send_candidate_references(candidate_references, candidate_id, oauth_string)

    candidate_get_response = requests.get(CandidateApiUrl.CANDIDATE % candidate_id,
                                          headers={'Authorization': oauth_string})

    if candidate_get_response.status_code is not requests.codes.ok:
        raise InvalidUsage(
            error_message=error_constants.CANDIDATE_GET['message'],
            error_code=error_constants.CANDIDATE_GET['code']
        )

    candidate = json.loads(candidate_get_response.content)

    return candidate


@upload_failed_IO
@contract
def get_cached_resume(resume_file, filename_str, cache_key):
    """
    Tries to retrieve processed resume data from redis or parses it and stores it.
    :param cStringIO resume_file:
    :param string filename_str:
    :rtype: (dict, bool)
    """
    cached_bg_xml = redis_store.get(cache_key)

    if cached_bg_xml:
        parsed_resume = {
            'candidate': parse_optic_xml(cached_bg_xml),
            'raw_response': cached_bg_xml
        }
        logger.info('ResumeParsingService::INFO - BG data for {} loaded with key {}'.format(
            filename_str, cache_key_from_file))
        return parsed_resume

    return False
