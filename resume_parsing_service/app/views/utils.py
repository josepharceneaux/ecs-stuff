"""Utilities related to the parsing of resumes."""
# pylint: disable=wrong-import-position, fixme
__author__ = 'erikfarmer'
# Standard Library
import json
# Third Party
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InvalidUsage, InternalServerError
from resume_parsing_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl


def create_parsed_resume_candidate(candidate_dict, formatted_token_str):
    """
    Sends candidate dict to candidate service POST and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return requests.response
    """
    try:
        create_response = requests.post(CandidateApiUrl.CANDIDATES,
                                        timeout=20,
                                        data=json.dumps({'candidates': [candidate_dict]}),
                                        headers={'Authorization': formatted_token_str,
                                                 'Content-Type': 'application/json'})
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
        logger.exception("create_parsed_resume_candidate. Could not reach CandidateService POST")
        raise InternalServerError("Unable to reach Candidates API in during candidate creation")
    if create_response.status_code in xrange(500, 511):
        raise InternalServerError('Error in response from candidate service during creation')
    return create_response


def update_candidate_from_resume(candidate_dict, formatted_token_str):
    """
    Sends candidate dict to candidate service PATCH and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return requests.response
    """
    try:
        update_response = requests.patch(CandidateApiUrl.CANDIDATES,
                                         timeout=20,
                                         data=json.dumps({'candidates': [candidate_dict]}),
                                         headers={'Authorization': formatted_token_str,
                                                  'Content-Type': 'application/json'})
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
        logger.exception("update_candidate_from_resume. Could not reach CandidateService PATCH")
        raise InternalServerError("Unable to reach Candidates API in during candidate update")
    if update_response.status_code is not requests.codes.ok:
        logger.warn("Unable to update candidate due to response code: {}".format(
            update_response.status_code))
        raise InvalidUsage('Error in response from candidate service during update')
    return update_response


#TODO: write tests for this.
def get_users_talent_pools(formatted_token_str):
    """
    Uses the candidate pool service to get talent pools of a user's domain via their token.
    :param str formatted_token_str: "bearer foo" formatted string; as it appears in header.
    :return: List of talent pools ids
    :rtype: list
    """
    try:
        talent_pool_request = requests.get(CandidatePoolApiUrl.TALENT_POOLS,
                                           headers={'Authorization': formatted_token_str})
    except requests.exceptions.ConnectionError:
        raise InvalidUsage("ResumeParsingService could not reach CandidatePool API in "
                           "get_users_talent_pools")
    talent_pools_response = json.loads(talent_pool_request.content)
    if 'error' in talent_pools_response:
        raise InvalidUsage(error_message=talent_pools_response['error'].get(
            'message', 'Error in getting user talent pools.'))
    return [talent_pool['id'] for talent_pool in talent_pools_response['talent_pools']]
