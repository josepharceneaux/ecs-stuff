"""Utilities related to the parsing of resumes."""
__author__ = 'erikfarmer'
import json
import requests
from flask import current_app as app
from resume_parsing_service.common.routes import CandidateApi

def create_candidate_from_parsed_resume(candidate_dict, oauth_token):
    """Sends candidate dict to candidate service and returns response. """
    payload = json.dumps({'candidates': [candidate_dict]})
    r = requests.post(CandidateApi.CANDIDATES, data=payload,
                      headers={'Authorization': oauth_token})
    response_body = r.content
    return response_body
