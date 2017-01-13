import pytz
from flask_restful import Resource
from flask import request, Blueprint
from user_service.common.routes import UserServiceApi
from user_service.common.error_handling import *
from user_service.common.talent_api import TalentApi
from user_service.common.utils.validators import is_number
from user_service.common.models.user import User, Domain, UserGroup, db, Role, Permission
from user_service.common.utils.auth_utils import require_oauth, require_any_permission, require_all_permissions
from user_service.user_app.user_service_utilties import get_users_stats_from_mixpanel


class GetAllRolesApi(Resource):

    decorators = [require_oauth()]
    # Access token decorator

    @require_all_permissions(Permission.PermissionNames.CAN_GET_USER_ROLE)
    def get(self, **kwargs):
        """
        GET /users/roles Fetch all roles in the system which can be assigned to a user
        :param kwargs:
        :return:
        """
        return {"roles": [{'id': role_object.id, 'name': role_object.name} for role_object in Role.query.all()]}


class UserRolesApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_USER_ROLE)
    def get(self, **kwargs):
        """
        GET /users/<user_id>/roles Fetch all permissions of a user

        :return A dictionary containing role Name and permissions of that role
        :rtype: dict
        """

        requested_user_id = kwargs.get('user_id')
        requested_user = User.query.get(requested_user_id)

        if not requested_user:
            raise NotFoundError("User with user_id %s doesn't exist" % requested_user_id)

        if (request.user.role.name == 'USER' and requested_user.id != request.user.id) or (
                        request.user.role.name != 'TALENT_ADMIN' and requested_user.domain_id != request.user.domain_id):
            raise UnauthorizedError("User %s doesn't have appropriate permission to get roles of user %s" % (
                request.user.id, requested_user.id))

        # GET all roles of given user
        permissions = [permission.name for permission in requested_user.role.get_all_permissions_of_role()]
        return {"role_name": requested_user.role.name, "permissions": permissions}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_USER_ROLE)
    def put(self, **kwargs):
        """
        POST /users/<user_id>/roles Add given roles to a user

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_user_id = kwargs.get('user_id')
        requested_user = User.query.get(requested_user_id)

        if not requested_user:
            raise NotFoundError("User with user_id %s doesn't exist" % requested_user_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'role' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        role = posted_data.get('role', '')
        if is_number(role):
            role_object = Role.query.get(int(role))
            if role_object:
                role_id = role
                role_name = role_object.name
            else:
                raise NotFoundError("Role with id:%s doesn't exist in database" % role)
        else:
            role_object = Role.get_by_name(role)
            if role_object:
                role_id = role_object.id
                role_name = role_object.name
            else:
                raise NotFoundError("Role with name:%s doesn't exist in database" % role)

        if request.user.role.name != 'TALENT_ADMIN' and (requested_user.domain_id != request.user.domain_id or role_name == 'TALENT_ADMIN'):
            raise UnauthorizedError("User %s doesn't have appropriate permission to get roles of user %s" % (
                request.user.id, requested_user.id))

        requested_user.role_id = role_id
        db.session.commit()

        return '', 201


class UserGroupsApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAIN_GROUPS)
    def get(self, **kwargs):
        """
        GET /groups/<group_id>/users?include_stats=True     Fetch all users in a user_group and also include stats

        :return A dictionary containing id and lastName of all users of a user_group
        :rtype: dict
        """

        requested_group_id = kwargs.get('group_id')
        include_stats_flag = request.args.get('include_stats', False)

        requested_group = UserGroup.query.get(requested_group_id)

        if not requested_group:
            raise NotFoundError("Group with group_id %s doesn't exist" % requested_group_id)

        if request.user.role.name != 'TALENT_ADMIN' and requested_group.domain_id != request.user.domain_id:
            raise UnauthorizedError("User %s doesn't have appropriate permission to add users to a "
                                    "group %s" % (request.user.id, requested_group_id))

        users_data_dict = {user.id: user.to_dict() for user in UserGroup.all_users_of_group(requested_group_id)}
        return {"users": get_users_stats_from_mixpanel(users_data_dict, False, include_stats_flag).values()}

    @require_any_permission(Permission.PermissionNames.CAN_ADD_DOMAIN_GROUPS)
    def post(self, **kwargs):
        """
        POST /groups/<group_id>/users Add users in a given user_group

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_group_id = kwargs.get('group_id')
        requested_group = UserGroup.query.get(requested_group_id)

        if not requested_group:
            raise NotFoundError("Group with group_id %s doesn't exist" % requested_group_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'user_ids' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        if request.user.role.name != 'TALENT_ADMIN' and requested_group.domain_id != request.user.domain_id:
            raise UnauthorizedError("User %s doesn't have appropriate permission to add users to a "
                                    "group %s" % (request.user.id, requested_group_id))

        UserGroup.add_users_to_group(requested_group, posted_data.get('user_ids'))
        return '', 201


class DomainGroupsApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAIN_GROUPS)
    def get(self, **kwargs):
        """
        GET /domain/<domain_id>/groups Fetch all user_groups of a given domain

        :return A dictionary containing id and name of all user_groups of a given domain
        :rtype: dict
        """

        requested_domain_id = kwargs.get('domain_id')
        requested_domain = Domain.query.get(requested_domain_id)

        if not requested_domain:
            raise NotFoundError("Domain with domain_id %s doesn't exist" % requested_domain_id)

        if request.user.role.name != 'TALENT_ADMIN' and requested_domain_id != request.user.domain_id:
            raise UnauthorizedError("User %s doesn't have appropriate permission to get all user_groups "
                                    "of domain %s" % (request.user.id, requested_domain_id))

        all_user_groups_of_domain = UserGroup.all_groups_of_domain(requested_domain_id)
        return {"user_groups": [{'id': user_group.id, 'name': user_group.name} for user_group in
                                all_user_groups_of_domain]}

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_DOMAIN_GROUPS)
    def post(self, **kwargs):
        """
        POST /domain/<domain_id>/groups Add user_groups to a given domain

        :return A dictionary containing ids of user_groups added to given domain
        :rtype: dict
        """

        requested_domain_id = kwargs.get('domain_id')
        requested_domain = Domain.query.get(requested_domain_id)

        if not requested_domain:
            raise NotFoundError("Domain with domain_id %s doesn't exist" % requested_domain_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'groups' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        if request.user.role.name != 'TALENT_ADMIN' and requested_domain_id != request.user.domain_id:
            raise UnauthorizedError("User %s doesn't have appropriate permission to add user_groups "
                                    "to domain %s" % (request.user.id, requested_domain_id))

        user_groups = UserGroup.add_groups(posted_data.get('groups'), requested_domain_id)
        return {'user_groups': [user_group.id for user_group in user_groups]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAIN_GROUPS)
    def put(self, **kwargs):
        """
        PUT /domain/groups/<group_id> Edit a user group with given group_id

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_group_id = kwargs.get('group_id')
        requested_group = UserGroup.query.get(requested_group_id)

        if not requested_group:
            raise NotFoundError("User Group with id %s doesn't exist" % requested_group_id)

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        if request.user.role.name != 'TALENT_ADMIN' and requested_group.domain_id != request.user.domain_id:
            raise UnauthorizedError("User %s doesn't have appropriate permission to edit user_groups %s" % (
                request.user.id, requested_group.name))

        name = posted_data.get('name')
        description = posted_data.get('description')

        if not name and not description:
            raise InvalidUsage("Neither name nor description is provided")

        if name and not UserGroup.query.filter_by(name=name, domain_id=requested_group.domain_id).all():
            requested_group.name = name
        elif name:
            raise InvalidUsage("User group '%s' already exists in domain %s" % (name, requested_group.domain_id))

        if description:
            requested_group.description = description

        db.session.commit()
        return '', 201

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_DOMAIN_GROUPS)
    def delete(self, **kwargs):
        """
        DELETE /domain/<domain_id>/groups Remove user_groups from a given domain

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_domain_id = kwargs.get('domain_id')
        requested_domain = Domain.query.get(requested_domain_id)

        if not requested_domain:
            raise NotFoundError("Domain with domain_id %s doesn't exist" % requested_domain_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'groups' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        if request.user.role.name != 'TALENT_ADMIN' and requested_domain_id != request.user.domain_id:
            raise UnauthorizedError("User %s doesn't have appropriate permission to remove user_groups "
                                    "from domain %s" % (request.user.id, requested_domain_id))

        UserGroup.delete_groups(requested_domain_id, posted_data.get('groups'))
        return '', 200


groups_and_roles_blueprint = Blueprint('groups_and_roles_api', __name__)
api = TalentApi(groups_and_roles_blueprint)
api.add_resource(UserRolesApi, UserServiceApi.USER_ROLES)
api.add_resource(GetAllRolesApi, UserServiceApi.ALL_ROLES)
api.add_resource(UserGroupsApi, UserServiceApi.USER_GROUPS)
api.add_resource(DomainGroupsApi, UserServiceApi.DOMAIN_GROUPS, UserServiceApi.DOMAIN_GROUPS_UPDATE)