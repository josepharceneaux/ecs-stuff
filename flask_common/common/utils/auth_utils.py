"""Helper functions related to the authentication of GT users."""
__author__ = 'erikfarmer'

# Standard Library
import datetime
from functools import wraps
import json
# Third Party
import requests
# Application/Module Specific
from ..utils.handy_functions import random_letter_digit_string
from flask import current_app as app
from flask import request
from ..models.user import *
from ..error_handling import *


def require_oauth(func):
    @wraps(func)
    def authenticate(*args, **kwargs):
        """
        This method will verify Authorization header of request using getTalent AuthService and will set
        request.user and request.oauth_token
        """
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
        try:
            response = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
        except Exception as e:
            raise InternalServerError(error_message=e.message)
        if response.status_code == 429:
            raise UnauthorizedError(error_message='You have exceeded the access limit of this API')
        elif not response.ok:
            error_body = response.json()
            if error_body['error']:
                raise UnauthorizedError(error_message=error_body['error']['message'], error_code=error_body['error']['code'])
            else:
                raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
        else:
            valid_user_id = response.json().get('user_id')
            request.user = User.query.get(valid_user_id)
            request.oauth_token = oauth_token
            return func(*args, **kwargs)
    return authenticate


def require_all_roles(*role_names):
    """ This method ensures that user should have all roles given in roles list"""
    def domain_roles(func):
        @wraps(func)
        def authenticate_roles(*args, **kwargs):
            if not role_names:
                # Roles list is empty so it means func is not roles protected
                return func(*args, **kwargs)
            user_roles = [DomainRole.query.get(user_role.role_id).role_name for user_role in
                          UserScopedRoles.get_all_roles_of_user(request.user.id)]
            for role_name in role_names:
                if role_name not in user_roles:
                    raise UnauthorizedError(error_message="User doesn't have appropriate permissions to "
                                                          "perform this operation")
            return func(*args, **kwargs)
        return authenticate_roles
    return domain_roles


def require_any_role(*role_names):
    """
    This method ensures that user should have at least one role from given roles list and set
    request.domain_independent_role to true if user has some domain independent (ADMIN) role
    """
    def domain_roles(func):
        @wraps(func)
        def authenticate_roles(*args, **kwargs):
            user_roles = [DomainRole.query.get(user_role.role_id).role_name for user_role in
                          UserScopedRoles.get_all_roles_of_user(request.user.id)]
            user_roles.append('SELF')
            if not role_names:
                # Roles list is empty so it means func is not roles protected
                return func(*args, **kwargs)
            else:
                valid_domain_roles = []
                # Roles which a logged-in user possess
                for role_name in role_names:
                    if role_name in user_roles:
                        valid_domain_roles.append(role_name)
                if valid_domain_roles:
                        request.valid_domain_roles = valid_domain_roles
                        return func(*args, **kwargs)
                raise UnauthorizedError(error_message="User doesn't have appropriate permissions to "
                                                      "perform this operation")
        return authenticate_roles
    return domain_roles


# This should be deprecated now that there is as decorator and once decorator has improved error
# messages.
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
    r = requests.get(app.config['OAUTH_AUTHORIZE_URI'], headers={'Authorization': 'bearer {}'.format(oauth_token)})
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
                  expires=datetime.datetime.utcnow() + datetime.timedelta(hours=2))
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
