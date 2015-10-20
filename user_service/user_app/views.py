__author__ = 'ufarooqi'

from . import app
from common.models.user import *
from user_service.user_app import logger
from flask import request
from common.error_handling import *
from common.utils.auth_utils import require_oauth, accepted_roles, required_roles


# TODO this endpoint will be removed eventually as we have decorators for this purpose
@app.route('/roles/verify')
def verify_roles():
    user_id = request.args.get('user_id')
    role_name = request.args.get('role')
    if role_name and user_id:
        domain_role = DomainRole.get_by_name(role_name)
        user = User.query.get(user_id)
        if domain_role and user:
            role_id = domain_role.id
            all_roles_of_user = UserScopedRoles.get_all_roles_of_user(user_id)
            all_roles_of_user = [user_role.roleId for user_role in all_roles_of_user]
            domain_roles = [all_role.id for all_role in DomainRole.all()]
            # User is an admin(has all possible roles) or it has input role
            if domain_roles == all_roles_of_user or role_id in all_roles_of_user:
                return jsonify(success=True)
    return jsonify(success=False)


@app.route('/users/<int:user_id>/roles', methods=['POST', 'GET', 'DELETE'])
@require_oauth
@required_roles('ADMIN')
def user_scoped_roles(user_id):
    if request.method == 'GET':
        user_roles = UserScopedRoles.get_all_roles_of_user(user_id)
        return jsonify(dict(roles=[user_scoped_role.roleId for user_scoped_role in user_roles]))
    else:
        posted_data = request.get_json(silent=True)
        if posted_data:
            try:
                if request.method == 'POST':
                    UserScopedRoles.add_roles(user_id, posted_data.get('roles'))
                    return jsonify(success=True)
                else:
                    UserScopedRoles.delete_roles(user_id, posted_data.get('roles'))
                    return jsonify(success=True)
            except Exception as e:
                logger.exception(e.message)
                raise InvalidUsage(error_message=e.message)
        else:
            raise InvalidUsage(error_message='Request data is corrupt')


@app.route('/domain/<int:domain_id>/roles', methods=['GET'])
@require_oauth
@accepted_roles('ADMIN', 'DOMAIN_ADMIN')
def get_all_roles_of_domain(domain_id):
    # if user has any other role than ADMIN then it should belong to same domain as input domain_id
    if Domain.query.get(domain_id) and (request.domain_role == 'ADMIN' or (request.user.domain_id == domain_id)):
        all_roles_of_domain = DomainRole.all_roles_of_domain(domain_id)
        return jsonify(dict(roles=[{'id': domain_role.id, 'name': domain_role.roleName} for
                                   domain_role in all_roles_of_domain]))
    else:
        raise InvalidUsage(error_message='Either domain_id is invalid or it is different than that of logged-in user')


@app.route('/groups/<int:group_id>/users', methods=['POST', 'GET'])
@require_oauth
@accepted_roles('ADMIN', 'DOMAIN_ADMIN')
def user_groups(group_id):
    user_group = UserGroup.query.get(group_id)
    if user_group and (request.domain_role == 'ADMIN' or request.user.domain_id == user_group.domain_id):
        if request.method == 'GET':
            # Get all users of group
            all_users_of_group = UserGroup.all_users_of_group(group_id)
            return jsonify(dict(users=[{'id': user.id, 'lastName': user.last_name} for user in all_users_of_group]))
        else:
            posted_data = request.get_json(silent=True)
            if posted_data:
                try:
                    UserGroup.add_users_to_group(group_id, posted_data.get('user_ids'))
                    return jsonify(success=True)
                except Exception as e:
                    logger.exception(e)
                    raise InvalidUsage(error_message=e.message)
            else:
                raise InvalidUsage(error_message='Request data is corrupt')
    else:
        raise InvalidUsage(error_message='Either group_id is invalid or domain of \
                                            this group is different than that of user')


@app.route('/groups', methods=['GET', 'POST', 'DELETE'])
@require_oauth
@accepted_roles('ADMIN', 'DOMAIN_ADMIN')
def domain_groups():
    if request.method == 'GET':
        # Get all groups of a domain
        domain_id = request.args.get('domain_id') or request.user.domain_id
        if Domain.query.get(domain_id) and (request.domain_role == 'ADMIN' or (request.user.domain_id == domain_id)):
            all_user_groups_of_domain = UserGroup.all_groups_of_domain(domain_id)
            return jsonify(dict(user_groups=[{'id': user_group.id, 'name': user_group.name} for user_group in
                                             all_user_groups_of_domain]))
        else:
            raise InvalidUsage(error_message='Either domain_id is invalid or it \
                                                is different than that of logged-in user')
    posted_data = request.get_json(silent=True)
    if posted_data:
        try:
            domain_id = posted_data.get('domain_id') or request.user.domain_id
            if Domain.query.get(domain_id) and (request.domain_role == 'ADMIN' or (request.user.domain_id == domain_id)):
                if request.method == 'POST':
                    groups = posted_data.get('groups')
                    UserGroup.add_groups(groups, domain_id)
                    return jsonify(success=True)
                else:
                    # Delete groups with given group_ids
                    UserGroup.delete_groups(domain_id, posted_data.get('groups'))
                    return jsonify(success=True)
            else:
                raise InvalidUsage(error_message='Either domain_id is invalid or it \
                                                    is different than that of logged-in user')
        except Exception as e:
            logger.exception(e)
            raise InvalidUsage(error_message=e.message)
    else:
        raise InvalidUsage(error_message='Request data is corrupt')
