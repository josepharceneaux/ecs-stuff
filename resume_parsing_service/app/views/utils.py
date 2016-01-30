"""Utilities related to the parsing of resumes."""
__author__ = 'erikfarmer'
import json
import requests
from resume_parsing_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl

def create_parsed_resume_candidate(candidate_dict, formatted_token_str):
    """
    Sends candidate dict to candidate service and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return requests.response
    """
    candidate_response = requests.post(CandidateApiUrl.CANDIDATES,
                                       data=json.dumps({'candidates': [candidate_dict]}),
                                       headers={'Authorization': formatted_token_str,
                                                'Content-Type': 'application/json'})
    response_body = candidate_response.content
    return response_body


#TODO: write tests for this.
def get_users_talent_pools(formatted_token_str):
    #TODO: add bad request handlet here.
    talent_pool_request = requests.get(CandidatePoolApiUrl.TALENT_POOLS,
                                       headers={'Authorization': formatted_token_str})
    talent_pools = json.loads(talent_pool_request.content)
    return [talent_pool['id'] for talent_pool in talent_pools['talent_pools']]
