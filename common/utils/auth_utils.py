"""Helper functions related to the authentication of GT users."""
__author__ = 'erikfarmer'
# Standard Library
from datetime import datetime
from datetime import timedelta
import json
# Third Party
import requests
# Application/Module Specific
from flask import current_app as app
from common.models.user import Token
from common.utils.handy_functions import random_letter_digit_string


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
    r = requests.get(app.config['OAUTH_AUTHORIZE_URI'], headers={'Authorization': oauth_token})
    if r.status_code != 200:
        return {'error': {'code': 3, 'message': 'Not authorized', 'http_code': 401}}
    valid_user_id = json.loads(r.text).get('user_id')
    if not valid_user_id:
        return {'error': {'code': 25,
                          'message': "Access token is invalid. Please refresh your token"},
                          'http_code': 400}
    return {'user_id': valid_user_id}


def get_token_by_client_and_user(client_id, user_id, db):
    # Fetches an Oauth2 token given a client_id/user_id.
    token = db.session.query(Token).filter_by(client_id=client_id, user_id=user_id).first()
    if not token:
        token = create_token(client_id, user_id, db)
    return token


def create_token(client_id, user_id, db):
    # Creates an Oauth2 token given a client_id/user_id.
    token = Token(client_id=client_id, user_id=user_id, token_type='Bearer',
                  access_token=random_letter_digit_string(255),
                  refresh_token=random_letter_digit_string(255),
                  expires=datetime.utcnow() + timedelta(hours=2))
    db.session.add(token)
    db.session.commit()
    return token


def refresh_expired_token(token, client_id, client_secret):
    # Sends a refresh request to the Oauth2 server.
    payload = {'grant_type': 'refresh_token', 'client_id': client_id,
               'client_secret': client_secret, 'refresh_token': token.refresh_token}
    r = requests.post(app.config['OAUTH_TOKEN_URI'], data=payload)
    # TODO: Add bad request handling.
    return json.loads(r.text)['access_token']