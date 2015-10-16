"""Helper functions related to the authentication of GT users."""
__author__ = 'erikfarmer'

from flask import current_app as app
from flask import request, jsonify
from common.models.user import *
import requests
import json
from functools import wraps


def require_oauth(func):
    @wraps(func)
    def authenticate(*args, **kwargs):
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            return jsonify({'error': {'message': 'No Auth header set'}}), 400
        r = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
        if r.status_code != 200:
            error_body = json.loads(r.text)
            if error_body['error']:
                return jsonify(error_body), 401
            else:
                return jsonify({'error': {'code': 3, 'message': 'Not authorized'}}), 401
        valid_user_id = json.loads(r.text).get('user_id')
        if not valid_user_id or not User.query.get(valid_user_id):
            return jsonify({'error': {'message': 'Oauth did not provide a valid user_id'}}), 400
        request.user = User.query.get(valid_user_id)
        request.oauth_token = oauth_token
        return func(*args, **kwargs)
    return authenticate


def required_roles(*roles):
    def domain_roles(func):
        @wraps(func)
        def authenticate_roles(*args, **kwargs):
            user_roles = UserScopedRoles.get_all_roles_of_user(request.user.id).get('roles')
            for role in roles:
                domain_role = DomainRole.get_by_name(role) or ''
                if not domain_role or domain_role.id not in user_roles:
                    return jsonify({'error': {'message': "User doesn't have appropriate permissions to "
                                                         "perform this operation"}}), 401
            return func(*args, **kwargs)
        return authenticate_roles
    return domain_roles


def accepted_roles(*roles):
    def domain_roles(func):
        @wraps(func)
        def authenticate_roles(*args, **kwargs):
            user_roles = UserScopedRoles.get_all_roles_of_user(request.user.id).get('roles')
            for role in roles:
                domain_role = DomainRole.get_by_name(role) or ''
                if domain_role and domain_role.id in user_roles:
                    return func(*args, **kwargs)
            return jsonify({'error': {'message': "User doesn't have appropriate permissions to "
                                                 "perform this operation"}}), 401
        return authenticate_roles
    return domain_roles


def authenticate_oauth_user(request):
    """
    :param request: (object) flask request object
    :return:
    """
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