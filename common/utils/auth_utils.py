"""Helper functions related to the authentication of GT users."""
__author__ = 'erikfarmer'

import json
import requests
from flask import current_app as app


def authenticate_oauth_user(request, token=None):
    """
    :param flask.wrappers.Request request: Flask Request object
    :return:
    """
    if token:
        oauth_token = token
    else:
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            return {'error': {'code': None, 'message':'No Authorization set', 'http_code': 400}}
    r = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
    if r.status_code != 200:
        return {'error': {'code': 3, 'message': 'Not authorized', 'http_code': 401}}
    valid_user_id = json.loads(r.text).get('user_id')
    if not valid_user_id:
        return {'error': {'code': 25,
                          'message': "Access token is invalid. Please refresh your token"},
                          'http_code': 400}
    return {'user_id': valid_user_id}