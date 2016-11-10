"""Utilities related to the parsing of resumes."""
# pylint: disable=wrong-import-position, fixme, import-error
__author__ = 'erikfarmer'
# Standard Library
import hashlib
import json
import re
from cStringIO import StringIO
# Third Party
from contracts import contract
from flask import current_app
import boto3
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.common.error_handling import InvalidUsage, InternalServerError
from resume_parsing_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl
from resume_parsing_service.common.utils.talent_s3 import boto3_get_file


@contract
def create_parsed_resume_candidate(candidate_dict, formatted_token_str):
    """
    Sends candidate dict to candidate service POST and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param string formatted_token_str: string in format 'Bearer foo'.
    :return: Tuple stating if candidate was created and the corresponding id.
    :rtype: tuple(bool, int|long)
    """
    try:
        create_response = requests.post(CandidateApiUrl.CANDIDATES,
                                        timeout=20,
                                        data=json.dumps({'candidates': [candidate_dict]}),
                                        headers={'Authorization': formatted_token_str,
                                                 'Content-Type': 'application/json'})

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("create_parsed_resume_candidate. Could not reach CandidateService POST")
        raise InternalServerError(
            error_message=error_constants.CANDIDATE_POST_CONNECTION['message'],
            error_code=error_constants.CANDIDATE_POST_CONNECTION['code']
        )

    # Handle bad responses from Candidate Service.
    if create_response.status_code in xrange(500, 511):
        logger.error('Error in response from candidate service during creation: {}'.format(
            create_response)
        )
        raise InternalServerError(
            error_message=error_constants.CANDIDATE_5XX['message'],
            error_code=error_constants.CANDIDATE_5XX['code']
        )

    response_dict = json.loads(create_response.content)

    # Handle other non 201 responses.
    if create_response.status_code is not requests.codes.created:

        #If a candidate has been created already it will provide an id.
        existing_candidate_id = response_dict.get('error', {}).get('id')

        if existing_candidate_id:
            return False, existing_candidate_id

        # If there was an issue with candidate creation we want to forward the error message and
        # the error code supplied by Candidate Service.
        else:
            candidate_service_error = response_dict.get('error', {}).get('message')
            logger.error(candidate_service_error)

            raise InvalidUsage(
                error_message=error_constants.CANDIDATE_POST_ERROR['message'],
                error_code=error_constants.CANDIDATE_POST_ERROR['code']
            )



    # Candidate was created. Return bool and id
    else:
        candidate_id = response_dict.get('candidates')[0]['id']
        logger.debug('Candidate created with id: {}'.format(candidate_id))
        return True, candidate_id


@contract
def update_candidate_from_resume(candidate_dict, formatted_token_str, filename_str):
    """
    Sends candidate dict to candidate service PATCH and returns response. If the update is not
    successfull it will raise an error.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param unicode formatted_token_str: string in format 'Bearer foo'.
    :return: Returns True if candidate is updated, else exception is raised.
    :rtype: bool
    """
    try:
        update_response = requests.patch(CandidateApiUrl.CANDIDATES,
                                         timeout=20,
                                         data=json.dumps({'candidates': [candidate_dict]}),
                                         headers={'Authorization': formatted_token_str,
                                                  'Content-Type': 'application/json'})
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("update_candidate_from_resume. Could not reach CandidateService PATCH")
        raise InternalServerError(
            error_message=error_constants.CANDIDATE_PATCH_CONNECTION['message'],
            error_code=error_constants.CANDIDATE_PATCH_CONNECTION['code']
        )

    if update_response.status_code is not requests.codes.ok:
        logger.info(
            "ResumetoCandidateError. {} received from CandidateService (update). File: {}".format(
                update_response.status_code, filename_str
            )
        )

        raise InternalServerError(
            error_message=error_constants.CANDIDATE_PATCH_GENERIC['message'],
            error_code=error_constants.CANDIDATE_PATCH_GENERIC['code']
        )

    response_dict = json.loads(update_response.content)
    candidate_id = response_dict.get('candidates')[0]['id']
    logger.debug('Candidate updated with id: {}'.format(candidate_id))

    return True


@contract
def send_candidate_references(candidate_references, candidate_id, oauth_string):
    """
    Makes an attempt to create references for a candidate using their id. Failure does not raise an
    exception as this would prevent the candidate creation life cycle, but instead logs the issue.
    :param string candidate_references:
    :param string candidate_id:
    :param string oauth_string:
    :return None:
    """
    post_body = {
        'candidate_references': [
            {'comments': candidate_references}
        ]
    }

    try:
        references_response = requests.post(
            CandidateApiUrl.REFERENCES % candidate_id, data=json.dumps(post_body),
            headers={'Authorization': oauth_string,
                     'Content-Type': 'application/json'})

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.warn(
            "process_resume. Connection error creating candidate {} references.".format(candidate_id))

    if references_response.status_code is not requests.codes.created:
        logger.warn("process_resume. Error creating candidate {} references. {}".format(
            candidate_id, references_response.content))


@contract
def get_users_talent_pools(formatted_token_str):
    """
    Uses the candidate pool service to get talent pools of a user's domain via their token.
    :param string formatted_token_str: "bearer foo" formatted string; as it appears in header.
    :return: List of talent pools ids
    :rtype: list(int)
    """
    try:
        talent_pool_response = requests.get(CandidatePoolApiUrl.TALENT_POOLS,
                                            headers={'Authorization': formatted_token_str})
    except requests.exceptions.ConnectionError:
        logger.exception("ResumeParsingService could not reach CandidatePool API in get_users_talent_pools")
        raise InternalServerError(
            error_message=error_constants.TALENT_POOLS_GET['message'],
            error_code=error_constants.TALENT_POOLS_GET['code']
        )

    talent_pools_response = json.loads(talent_pool_response.content)

    if 'error' in talent_pools_response:
        logger.error(
            talent_pools_response['error'].get('message', 'Error in getting user talent pools.')
        )

        raise InvalidUsage(
            error_message=error_constants.TALENT_POOLS_ERROR['message'],
            error_code=error_constants.TALENT_POOLS_ERROR['code']
        )

    try:
        return [talent_pools_response['talent_pools'][0]['id']]

    except IndexError:
        return []


def gen_hash_from_file(_file):
    """Handy function for creating file hashes. Used as redis keys to store parsed resumes."""
    return hashlib.md5(_file.getvalue()).hexdigest()


def resume_file_from_params(parse_params):
    """
    Obtains a resume from the POST JSON data.
    :param parse_params:
    :return:
    """
    filepicker_key = parse_params.get('filepicker_key')

    if filepicker_key:
        resume_bucket = current_app.config['S3_FILEPICKER_BUCKET_NAME']
        resume_file = boto3_get_file(resume_bucket, filepicker_key)
    elif parse_params.get('filename'):
        resume_bin = parse_params.get('resume_file')
        resume_file = StringIO(resume_bin.read())
        resume_bin.close()

    else:
        raise InvalidUsage(
            error_message=error_constants.INVALID_ARGS['message'],
            error_code=error_constants.INVALID_ARGS['code']
        )

    return resume_file


def extra_skills_parsing(encoded_text):
    url = current_app.config["JD_URL"]
    payload = json.dumps({'text': encoded_text})
    try:
        skills_response = requests.post(url, data=payload)
    except requests.exceptions.ConnectionError:
        logger.exception("Unable to obtain extra skills from lambda call")

    loaded_response = json.loads(skills_response.content)
    return loaded_response.get('skills')


def string_scrubber(text):
    return re.sub(r"\s+", " ", text).strip()

def parse_email_from_string(text):
    address = re.compile(r"[a-zA-Z0-9\u00C0-\u017F`'_.+-]")
    at_sign = re.compile(r"@")
    domain = re.compile(r"[a-zA-Z0-9-]")
    end_domain = re.compile(r".[a-zA-Z0-9-.]+")
    regexes = (address, at_sign, domain, end_domain)
    pattern_combined = '+'.join(x.pattern for x in regexes)
    email =  re.search(pattern_combined, text)
    if email:
        return email.group(0)
    else:
        return None
