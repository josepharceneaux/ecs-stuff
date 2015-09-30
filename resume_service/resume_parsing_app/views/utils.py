"""Utilities related to the parsing of resumes."""

__author__ = 'erikfarmer'

import json
from urllib2 import Request
from urllib2 import urlopen

def create_candidate_from_parsed_resume(candidate_dict, oauth_token):
    payload = json.dumps({'candidates': [candidate_dict]})
    request = Request('http://127.0.0.1:8000/web/api/candidates.json', data=payload,
                      headers={'Authorization': oauth_token})
    response_body = urlopen(request).read()
    return response_body