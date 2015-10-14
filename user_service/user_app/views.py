__author__ = 'ufarooqi'

from . import app
from common.models.user import *
from user_service.user_app import logger
from flask import request, jsonify
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
            return jsonify({'error': {'message': 'Invalid Authorization'}}), 401
        valid_user_id = json.loads(r.text).get('user_id')
        if not valid_user_id:
            return jsonify({'error': {'message': 'Oauth did not provide a valid user_id'}}), 400
        return func(*args, **kwargs)
    return authenticate


@app.route('/')
def hello_world():
    return jsonify(good=True)


@app.route('/roles/verify')
def verify_roles():
    user_id = request.args.get('user_id')
    role_name = request.args.get('role')
    if role_name and user_id:
        domain_role = DomainRole.get_by_name(role_name)
        user = User.query.get(user_id)
        if domain_role and user:
            role_id = domain_role.id
            all_roles_of_user = UserScopedRoles.get_all_roles_of_user(user.id)['roles']
            # User is not an admin(role_id = 1) nor it contains input role
            if DomainRole.all() == all_roles_of_user or role_id in all_roles_of_user:
                return jsonify(success=True)
    return jsonify(success=False)


@app.route('/users/<int:user_id>/roles', methods=['POST', 'GET', 'DELETE'])
@require_oauth
def user_scoped_roles(user_id):
    if request.method == 'GET':
        return jsonify(UserScopedRoles.get_all_roles_of_user(user_id))
    else:
        posted_data = request.get_json(silent=True)
        if posted_data:
            try:
                if request.method == 'POST':
                    UserScopedRoles.add_roles(user_id, posted_data.get('roles'))
                    return jsonify(success=True)
                elif request.method == 'DELETE':
                    UserScopedRoles.delete_roles(user_id, posted_data.get('roles'))
                    return jsonify(success=True)
                else:
                    raise Exception("Invalid URL method %s" % request.method)
            except Exception as e:
                logger.error(e)
                return jsonify(error_message=e.message), 404
        else:
            return jsonify(error_message='Request data is corrupt'), 400


@app.route('/domain/<int:domain_id>/roles', methods=['GET'])
@require_oauth
def get_all_roles_of_domain(domain_id):
    if Domain.query.get(domain_id):
        return jsonify(DomainRole.all_roles_of_domain(domain_id))
