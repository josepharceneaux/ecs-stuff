"""Utilities related to the parsing of resumes."""
__author__ = 'erikfarmer'
import json
import requests
from resume_service.common.routes import CandidateApiUrl

def create_parsed_resume_candidate(candidate_dict, formatted_token_str):
    """
    Sends candidate dict to candidate service and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return requests.response
    """
    payload = json.dumps({'candidates': [candidate_dict]})
    candidate_response = requests.post(CandidateApiUrl.CANDIDATES, data=payload,
                                       headers={'Authorization': formatted_token_str})
    response_body = candidate_response.content
    return response_body
