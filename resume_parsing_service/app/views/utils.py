"""Utilities related to the parsing of resumes."""
# pylint: disable=wrong-import-position, fixme
__author__ = 'erikfarmer'
# Standard Library
import json
# Third Party
import requests
# Module Specific
from resume_parsing_service.common.error_handling import ResourceNotFound
from resume_parsing_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl

def create_parsed_resume_candidate(candidate_dict, formatted_token_str):
    """
    Sends candidate dict to candidate service and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return requests.response
    """
    try:
        candidate_response = requests.post(CandidateApiUrl.CANDIDATES,
                                           data=json.dumps({'candidates': [candidate_dict]}),
                                           headers={'Authorization': formatted_token_str,
                                                    'Content-Type': 'application/json'})
    except requests.exceptions.ConnectionError:
        raise ResourceNotFound("Resume Parsing service cannot reach Candidates API in "
                               "create_parsed_resume_candidate")
    response_body = candidate_response.content
    return response_body


#TODO: write tests for this.
def get_users_talent_pools(formatted_token_str):
    try:
        talent_pool_request = requests.get(CandidatePoolApiUrl.TALENT_POOLS,
                                           headers={'Authorization': formatted_token_str})
    except requests.exceptions.ConnectionError:
        raise ResourceNotFound("ResumeParsingService could not reach CandidatePool API in "
                               "get_users_talent_pools")
    talent_pools = json.loads(talent_pool_request.content)
    return [talent_pool['id'] for talent_pool in talent_pools['talent_pools']]
