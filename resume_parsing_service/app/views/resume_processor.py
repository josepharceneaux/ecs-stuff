"""Main resume parsing logic & functions."""
# pylint: disable=wrong-import-position, fixme, import-error
# Standard library
import json
# Third Party/Framework Specific.
import requests
from flask import current_app
# Module Specific
from resume_parsing_service.app import logger, redis_store
from resume_parsing_service.app.views.optic_parse_lib import parse_optic_xml
from resume_parsing_service.app.views.decorators import upload_failed_IO
from resume_parsing_service.app.views.parse_lib import parse_resume
from resume_parsing_service.app.views.utils import update_candidate_from_resume
from resume_parsing_service.app.views.utils import create_parsed_resume_candidate
from resume_parsing_service.app.views.utils import send_candidate_references
from resume_parsing_service.app.views.utils import gen_hash_from_file
from resume_parsing_service.app.views.utils import resume_file_from_params
from resume_parsing_service.common.error_handling import InvalidUsage
from resume_parsing_service.common.routes import CandidateApiUrl
from resume_parsing_service.common.utils.talent_s3 import boto3_put


IMAGE_FORMATS = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.dcx',
                 '.pcx', '.jp2', '.jpc', '.jb2', '.djvu', '.djv']
DOC_FORMATS = ['.pdf', '.doc', '.docx', '.rtf', '.txt']
RESUME_EXPIRE_TIME = 60 * 60 * 24 * 7  # one week in seconds.


def process_resume(parse_params):
    """
    Parses a resume based on a provided: filepicker key or binary, filename
    :param dict parse_params:
    :return: dict: {'candidate': {...}, 'raw': {...}}
    """

    # None may be explicitly passed so the normal .get('attr', default) doesn't apply here.
    create_candidate = parse_params.get('create_candidate', False)

    # We need to obtain/define the file from our params.
    resume_file = resume_file_from_params(parse_params)
    filename_str = parse_params['filename'] # This is always set by param_builders.py

    # Checks to see if we already have BG contents in Redis.
    parsed_resume = get_or_store_parsed_resume(resume_file, filename_str)

    if not create_candidate:
        return parsed_resume

    talent_pools = parse_params.get('talent_pools')
    # Talent pools are the ONLY thing required to create a candidate.
    if create_candidate and not talent_pools:
        raise InvalidUsage('Talent Pools required for candidate creation')

    oauth_string = parse_params.get('oauth')
    parsed_resume['candidate']['talent_pool_ids']['add'] = talent_pools

    # Upload resumes we want to create candidates from.
    try:
        resume_file.seek(0)
        bucket = current_app.config['S3_BUCKET_NAME']
        boto3_put(resume_file.read(), bucket, filename_str, 'OriginalFiles')
        parsed_resume['candidate']['resume_url'] = filename_str

    except Exception as e:
        logger.exception('Failure during s3 upload; reason: {}'.format(e.message))

    candidate_references = parsed_resume['candidate'].pop('references', None)
    candidate_created, candidate_id = create_parsed_resume_candidate(
        parsed_resume['candidate'], oauth_string, filename_str)

    if not candidate_created:
        # We must update!
        parsed_resume['candidate']['id'] = candidate_id
        candidate_updated = update_candidate_from_resume(
            parsed_resume['candidate'], oauth_string, filename_str)

    # References have their own endpoint and are not part of /candidates POSTed data.
    if candidate_references:
        send_candidate_references(candidate_references, candidate_id, oauth_string)

    candidate_get_response = requests.get(CandidateApiUrl.CANDIDATE % candidate_id,
                                          headers={'Authorization': oauth_string})

    if candidate_get_response.status_code is not requests.codes.ok:
        raise InvalidUsage(error_message='Error retrieving created candidate')

    candidate = json.loads(candidate_get_response.content)

    return candidate


@upload_failed_IO
def get_or_store_parsed_resume(resume_file, filename_str):
    """
    Tries to retrieve processed resume data from redis or parses it and stores it.
    :param resume_file:
    :param filename_str:
    :return:
    """
    cache_key_from_file = 'parsedResume_{}'.format(gen_hash_from_file(resume_file))
    cached_bg_xml = redis_store.get(cache_key_from_file)

    if cached_bg_xml:
        parsed_resume = {
            'candidate': parse_optic_xml(cached_bg_xml),
            'raw_response': cached_bg_xml
        }
        logger.info('BG data for {} loaded with key {}'.format(
            filename_str, cache_key_from_file))

    else:
        # Parse the resume if not hashed.
        logger.info('Couldn\'t find Resume {} in cache with hashed_key: {}'.format(filename_str,
                                                                                   cache_key_from_file))
        parsed_resume = parse_resume(resume_file, filename_str, cache_key_from_file)

    return parsed_resume
