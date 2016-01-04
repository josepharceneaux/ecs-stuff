"""Utilities related to the parsing of resumes."""
__author__ = 'erikfarmer'
import json
import requests
from flask import current_app as app

def create_candidate_from_parsed_resume(candidate_dict, oauth_token):
    """Sends candidate dict to candidate service and returns response. """
    payload = json.dumps({'candidates': [candidate_dict]})
    r = requests.post(app.config['CANDIDATE_CREATION_URI'], data=payload,
                      headers={'Authorization': oauth_token})
    response_body = r.content
    return response_body
