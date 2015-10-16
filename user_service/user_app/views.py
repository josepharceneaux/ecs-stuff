__author__ = 'ufarooqi'

from . import app
from common.models.user import *
from user_service.user_app import logger
from flask import request, jsonify
from common.utils.auth_utils import require_oauth, accepted_roles, required_roles


@app.route('/')
@require_oauth
def hello_world():
    user = request.oauth_token
    return jsonify(good=user)


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
@required_roles('ADMIN')
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
@accepted_roles('ADMIN', 'DOMAIN_ADMIN')
def get_all_roles_of_domain(domain_id):
    if Domain.query.get(domain_id):
        return jsonify(DomainRole.all_roles_of_domain(domain_id))


@app.route('/groups/<int:group_id>/users', methods=['POST', 'GET'])
@require_oauth
@accepted_roles('ADMIN', 'DOMAIN_ADMIN')
def user_groups(group_id):
    if request.method == 'GET':
        # Get all users of group
        return jsonify(UserGroups.all_users_of_group(group_id))
    else:
        posted_data = request.get_json(silent=True)
        if posted_data:
            try:
                if request.method == 'POST':
                    UserGroups.add_users_to_group(group_id, posted_data.get('user_ids'))
                    return jsonify(success=True)
                else:
                    raise Exception("Invalid URL method %s" % request.method)
            except Exception as e:
                logger.error(e)
                return jsonify(error_message=e.message), 404
        else:
            return jsonify(error_message='Request data is corrupt'), 400


@app.route('/groups', methods=['GET', 'POST', 'DELETE'])
@require_oauth
@accepted_roles('ADMIN', 'DOMAIN_ADMIN')
def domain_groups(group_id):
    if request.method == 'GET':
        # Get all groups of a domain
        return jsonify(UserGroups.all_groups_of_domain(request.user.domain_id))

    posted_data = request.get_json(silent=True)
    if posted_data:
        try:
            if request.method == 'POST':
                name = posted_data.get('group_name')
                description = posted_data.get('group_description') or ''
                domain_id = request.user.domain_id
                UserGroups.save(domain_id, name, description)
                return jsonify(success=True)
            if request.method == 'DELETE':
                # Delete groups with given group_ids
                UserGroups.delete_groups(request.user.domain_id, posted_data.get('group_ids'))
                return jsonify(success=True)
            else:
                raise Exception("Invalid URL method %s" % request.method)
        except Exception as e:
            logger.error(e)
            return jsonify(error_message=e.message), 404
    else:
        return jsonify(error_message='Request data is corrupt'), 400