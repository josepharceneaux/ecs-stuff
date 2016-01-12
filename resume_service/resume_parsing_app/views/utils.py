"""Utilities related to the parsing of resumes."""
__author__ = 'erikfarmer'
from resume_service.common.routes import CandidateApiUrl
import json
import requests

def create_candidate_from_parsed_resume(candidate_dict, token):
    """Sends candidate dict to candidate service and returns response. """
    payload = json.dumps({'candidates': [candidate_dict]})
    candidate_response = requests.post(CandidateApiUrl.CANDIDATES, data=payload,
                                       headers={'Authorization': 'bearer {}'.format(token)})
    response_body = candidate_response.content
    return response_body
