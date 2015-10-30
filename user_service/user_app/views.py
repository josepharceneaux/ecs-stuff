__author__ = 'ufarooqi'

from . import app
from common.models.user import *
from flask import request
from common.error_handling import *
from common.utils.auth_utils import require_oauth, require_any_role
from werkzeug.security import generate_password_hash, check_password_hash


# TODO this endpoint will be removed eventually as we have decorators for this purpose
@app.route('/roles/verify')
def verify_roles():
    user_id = request.args.get('user_id')
    role_name = request.args.get('role')
    if role_name and user_id:
        domain_role = DomainRole.get_by_name(role_name)
        user = User.query.get(user_id)
        if domain_role and user:
            all_role_ids_of_user = [user_role.role_id for user_role in UserScopedRoles.get_all_roles_of_user(user_id)]
            if domain_role.id in all_role_ids_of_user:
                return jsonify(success=True)
    return jsonify(success=False)


@app.route('/users/<int:user_id>/roles', methods=['POST', 'GET', 'DELETE'])
@require_oauth
@require_any_role('ADMIN', 'DOMAIN_ADMIN')
def user_scoped_roles(user_id):
    user = User.query.get(user_id)
    # if logged-in user has any other role than ADMIN then it should belong to same domain as input user
    if user and (request.is_admin_user or (request.user.domain_id == user.domain_id)):
        if request.method == 'GET':
            user_roles = UserScopedRoles.get_all_roles_of_user(user_id)
            return jsonify(dict(roles=[user_scoped_role.role_id for user_scoped_role in user_roles]))
        else:
            posted_data = request.get_json(silent=True)
            if posted_data:
                if request.method == 'POST':
                    UserScopedRoles.add_roles(user, request.is_admin_user, posted_data.get('roles'))
                    return jsonify(success=True)
                else:
                    UserScopedRoles.delete_roles(user, request.is_admin_user, posted_data.get('roles'))
                    return jsonify(success=True)
            else:
                raise InvalidUsage(error_message='Request data is corrupt')
    else:
        raise InvalidUsage(error_message='Either user_id is invalid or domain_id of user is \
                                            different than that of logged-in user')


@app.route('/domain/<int:domain_id>/roles', methods=['GET'])
@require_oauth
@require_any_role('ADMIN', 'DOMAIN_ADMIN')
def get_all_roles_of_domain(domain_id):
    # if logged-in user has any other role than ADMIN then it should belong to same domain as input domain_id
    if Domain.query.get(domain_id) and (request.is_admin_user or (request.user.domain_id == domain_id)):
        all_roles_of_domain = DomainRole.all_roles_of_domain(domain_id)
        return jsonify(dict(roles=[{'id': domain_role.id, 'name': domain_role.role_name} for
                                   domain_role in all_roles_of_domain]))
    else:
        raise InvalidUsage(error_message='Either domain_id is invalid or it is different than that of logged-in user')


@app.route('/groups/<int:group_id>/users', methods=['POST', 'GET'])
@require_oauth
@require_any_role('ADMIN', 'DOMAIN_ADMIN')
def user_groups(group_id):
    user_group = UserGroup.query.get(group_id)
    # if logged-in user has any other role than ADMIN then it should belong to same domain as input user_group
    if user_group and (request.is_admin_user or request.user.domain_id == user_group.domain_id):
        if request.method == 'GET':
            # Get all users of group
            all_users_of_group = UserGroup.all_users_of_group(group_id)
            return jsonify(dict(users=[{'id': user.id, 'lastName': user.last_name} for user in all_users_of_group]))
        else:
            posted_data = request.get_json(silent=True)
            if posted_data:
                UserGroup.add_users_to_group(user_group, posted_data.get('user_ids'))
                return jsonify(success=True)
            else:
                raise InvalidUsage(error_message='Request data is corrupt')
    else:
        raise InvalidUsage(error_message='Either group_id is invalid or domain of \
                                            this group is different than that of user')


@app.route('/domain/<int:domain_id>/groups', methods=['GET', 'POST', 'DELETE'])
@require_oauth
@require_any_role('ADMIN', 'DOMAIN_ADMIN')
def domain_groups(domain_id):
    # Get all groups of a domain
    if request.method == 'GET':
        # if logged-in user has any other role than ADMIN then it should belong to same domain as input domain_id
        if Domain.query.get(domain_id) and (request.is_admin_user or request.user.domain_id == domain_id):
            all_user_groups_of_domain = UserGroup.all_groups_of_domain(domain_id)
            return jsonify(dict(user_groups=[{'id': user_group.id, 'name': user_group.name} for user_group in
                                             all_user_groups_of_domain]))
        else:
            raise InvalidUsage(error_message='Either domain_id is invalid or it \
                                                is different than that of logged-in user')
    posted_data = request.get_json(silent=True)
    if posted_data:
        if request.method == 'POST':
            # if logged-in user has any other role than ADMIN then it should belong to same domain as input domain_id
            if Domain.query.get(domain_id) and (request.is_admin_user or request.user.domain_id == domain_id):
                groups = posted_data.get('groups')
                UserGroup.add_groups(groups, domain_id)
                return jsonify(success=True)
            else:
                raise InvalidUsage(error_message='Either domain_id is invalid or it \
                                            is different than that of logged-in user')
        else:
            # Delete groups with given group_ids
            UserGroup.delete_groups(request.user.domain_id, request.is_admin_user, posted_data.get('groups'))
            return jsonify(success=True)
    else:
        raise InvalidUsage(error_message='Request data is corrupt')


@app.route('/users/<int:user_id>/update_password', methods=['POST'])
@require_oauth
@require_any_role()
def update_password(user_id):
    """
    This endpoint will be used to update the password of a user given old password
    :param: int user_id: Id of user whose password is going to be updated
    :return: success message if password will be updated successfully
    :rtype: dict
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(error_message="User with user_id %s doesn't exist" % user_id)
    # Logged-in user should be either DOMAIN_ADMIN, ADMIN to update password or it can update its own password
    if user_id != request.user.id and not request.is_admin_user and ('DOMAIN_ADMIN' not in request.
            valid_domain_roles or user.domain_id != request.user.domain_id):
        raise UnauthorizedError('User %s is not allowed to update the password' % request.user.id)

    posted_data = request.get_json()
    if posted_data:
        old_password = posted_data.get('old_password', '')
        new_password = posted_data.get('new_password', '')
        if not old_password or not new_password:
            raise NotFoundError(error_message="Either old or new password is missing")
        old_password_hashed = user.password
        # If password is hashed in web2py app
        if 'pbkdf2:sha512:1000' not in old_password_hashed and old_password_hashed.count('$') == 2:
            (digest_alg, salt, hash_key) = user.password.split('$')
            old_password_hashed = 'pbkdf2:sha512:1000$%s$%s' % (salt, hash_key)
        if check_password_hash(old_password_hashed, old_password):
            # Change user's password
            user.password = generate_password_hash(new_password, method='pbkdf2:sha512')
            # Delete any tokens associated with him as password is changed now
            Token.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            return jsonify(dict(success="Your password has been changed successfully"))
        else:
            raise UnauthorizedError(error_message="Old password is not correct")
    else:
        raise InvalidUsage(error_message='No request data is found')
