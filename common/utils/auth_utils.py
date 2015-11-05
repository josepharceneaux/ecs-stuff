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
        """
        This method will verify Authorization header of request using getTalent AuthService and will set
        request.user and request.oauth_token
        """
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
        try:
            r = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
        except Exception as e:
            raise InternalServerError(error_message=e.message)
        if r.status_code == 429:
            raise UnauthorizedError(error_message='You have exceeded the access limit of this API')
        elif r.status_code != 429 and not r.ok:
            error_body = json.loads(r.text)
            if error_body['error']:
                raise UnauthorizedError(error_message=error_body['error']['message'], error_code=error_body['error']['code'])
            else:
                raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
        else:
            valid_user_id = json.loads(r.text).get('user_id')
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
            user_roles = UserScopedRoles.get_all_roles_of_user(request.user.id)
            user_roles = [user_role.role_id for user_role in user_roles]
            domain_roles = DomainRole.get_by_names(role_names) or ''
            for domain_role in domain_roles:
                if not domain_role or domain_role.id not in user_roles:
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
            if not role_names:
                # Roles list is empty so it means func is not roles protected
                request.valid_domain_roles = user_roles
                request.is_admin_user = True if 'ADMIN' in request.valid_domain_roles else False
                return func(*args, **kwargs)
            else:
                # Roles which a requesting user possess
                valid_domain_roles = []
                for role_name in role_names:
                    if role_name in user_roles:
                        valid_domain_roles.append(role_name)
                if valid_domain_roles:
                    request.valid_domain_roles = valid_domain_roles
                    request.is_admin_user = True if 'ADMIN' in valid_domain_roles else False
                    return func(*args, **kwargs)
                else:
                    raise UnauthorizedError(error_message="User doesn't have appropriate permissions to "
                                                          "perform this operation")
        return authenticate_roles
    return domain_roles
