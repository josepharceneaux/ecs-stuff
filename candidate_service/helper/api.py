from flask import request
from candidate_service.candidate_app import logger
import json


def parse_request_data():
    """
    :rtype:
    """
    request_data = ''
    try:
        request_data = request.data
        logger.info('%s:%s: Received request data: %s',
                    (request.url, request.method, request_data))
        body_dict = json.loads(request_data)
    except Exception:
        logger.info('%s:%s: Received request data: %s',
                    (request.url, request.method, request_data))
        return {'error': {'message': 'Unable to parse request data as JSON'}}, 400

    # Request data must be a JSON dict
    if not isinstance(body_dict, dict):
        return {'error': {'message': 'Request data must be a JSON dict'}}, 400

    # Request data cannot be empty
    if not any(body_dict):
        return {'error': {'message': 'Request data cannot be empty'}}, 400

    return body_dict
