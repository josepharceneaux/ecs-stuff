"""Helper functions related to the authentication of GT users."""
__author__ = 'erikfarmer'

from flask import current_app as app
from flask import request
from common.models.user import *
import requests
import json
from functools import wraps
from common.error_handling import *


def require_oauth(func):
    @wraps(func)
    def authenticate(*args, **kwargs):
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
        r = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
        if r.status_code != 200:
            error_body = json.loads(r.text)
            if error_body['error']:
                raise UnauthorizedError(error_message=error_body['error']['message'], error_code=error_body['error']['code'])
            else:
                raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
        valid_user_id = json.loads(r.text).get('user_id')
        request.user = User.query.get(valid_user_id)
        request.oauth_token = oauth_token
        return func(*args, **kwargs)
    return authenticate


def required_roles(*roles):
    def domain_roles(func):
        @wraps(func)
        def authenticate_roles(*args, **kwargs):
            user_roles = UserScopedRoles.get_all_roles_of_user(request.user.id)
            user_roles = [user_role.roleId for user_role in user_roles]
            for role in roles:
                domain_role = DomainRole.get_by_name(role) or ''
                if not domain_role or domain_role.id not in user_roles:
                    raise UnauthorizedError(error_message="User doesn't have appropriate permissions to \
                                                            perform this operation")
            return func(*args, **kwargs)
        return authenticate_roles
    return domain_roles


def accepted_roles(*roles):
    def domain_roles(func):
        @wraps(func)
        def authenticate_roles(*args, **kwargs):
            user_roles = UserScopedRoles.get_all_roles_of_user(request.user.id)
            user_roles = [user_role.roleId for user_role in user_roles]
            for role in roles:
                domain_role = DomainRole.get_by_name(role) or ''
                if domain_role and domain_role.id in user_roles:
                    request.domain_role = role
                    return func(*args, **kwargs)
            raise UnauthorizedError(error_message="User doesn't have appropriate permissions to \
                                                    perform this operation")
        return authenticate_roles
    return domain_roles
