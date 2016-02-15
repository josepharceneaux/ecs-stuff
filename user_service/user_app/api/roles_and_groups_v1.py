from flask_restful import Resource
from flask import request, Blueprint
from user_service.common.routes import UserServiceApi
from user_service.common.error_handling import *
from user_service.common.talent_api import TalentApi
from user_service.common.models.user import User, Domain, UserScopedRoles, UserGroup, db, DomainRole
from user_service.common.utils.auth_utils import require_oauth, require_any_role, require_all_roles


class UserScopedRolesApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_GET_USER_ROLES)
    def get(self, **kwargs):
        """
        GET /users/<user_id>/roles Fetch all roles of a user

        :return A dictionary containing role ids of all roles of a given user
        :rtype: dict
        """

        requested_user_id = kwargs.get('user_id')
        requested_user = User.query.get(requested_user_id)

        if not requested_user:
            raise NotFoundError(error_message="User with user_id %s doesn't exist" % requested_user_id)

        if requested_user.id != request.user.id and 'CAN_GET_USER_ROLES' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to get roles of user %s"
                                                  % (request.user.id, requested_user.id))

        if requested_user.domain_id != request.user.domain_id:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to get roles of user %s"
                                                  % (request.user.id, requested_user.id))

        # GET all roles of given user
        user_roles = UserScopedRoles.get_all_roles_of_user(requested_user_id)
        return {"roles": [user_scoped_role.role_id for user_scoped_role in user_roles]}

    @require_all_roles(DomainRole.Roles.CAN_ADD_USER_ROLES)
    def post(self, **kwargs):
        """
        POST /users/<user_id>/roles Add given roles to a user

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_user_id = kwargs.get('user_id')
        requested_user = User.query.get(requested_user_id)

        if not requested_user:
            raise NotFoundError(error_message="User with user_id %s doesn't exist" % requested_user_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'roles' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_user.domain_id != request.user.domain_id:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to add roles to user %s"
                                                  % (request.user.id, requested_user.id))

        UserScopedRoles.add_roles(requested_user, posted_data.get('roles'))
        return {"success_message": "All given roles have been added successfully"}

    @require_all_roles(DomainRole.Roles.CAN_DELETE_USER_ROLES)
    def delete(self, **kwargs):
        """
        DELETE /users/<user_id>/roles Remove given roles from a user

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_user_id = kwargs.get('user_id')
        requested_user = User.query.get(requested_user_id)

        if not requested_user:
            raise NotFoundError(error_message="User with user_id %s doesn't exist" % requested_user_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'roles' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_user.domain_id != request.user.domain_id:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to remove roles from "
                                                  "user %s" % (request.user.id, requested_user.id))

        UserScopedRoles.delete_roles(requested_user, posted_data.get('roles'))
        return {"success_message": "All given roles have been removed successfully"}


class UserGroupsApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    @require_any_role(DomainRole.Roles.CAN_GET_GROUP_USERS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def get(self, **kwargs):
        """
        GET /groups/<group_id>/users Fetch all users in a user_group

        :return A dictionary containing id and lastName of all users of a user_group
        :rtype: dict
        """

        requested_group_id = kwargs.get('group_id')
        requested_group = UserGroup.query.get(requested_group_id)

        if not requested_group:
            raise NotFoundError(error_message="Group with group_id %s doesn't exist" % requested_group_id)

        if requested_group.domain_id != request.user.domain_id and not request.is_admin_user:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to get all users of a "
                                                  "group %s" % (request.user.id, requested_group_id))

        all_users_of_group = UserGroup.all_users_of_group(requested_group_id)
        return {"users": [{'id': user.id, 'lastName': user.last_name} for user in all_users_of_group]}

    @require_any_role(DomainRole.Roles.CAN_ADD_GROUP_USERS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def post(self, **kwargs):
        """
        POST /groups/<group_id>/users Add users in a given user_group

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_group_id = kwargs.get('group_id')
        requested_group = UserGroup.query.get(requested_group_id)

        if not requested_group:
            raise NotFoundError(error_message="Group with group_id %s doesn't exist" % requested_group_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'user_ids' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_group.domain_id != request.user.domain_id and not request.is_admin_user:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to add users to a "
                                                  "group %s" % (request.user.id, requested_group_id))

        UserGroup.add_users_to_group(requested_group, posted_data.get('user_ids'))
        return {"success_message": "All given users have been added successfully in user group"}


class DomainGroupsApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    @require_any_role(DomainRole.Roles.CAN_GET_DOMAIN_GROUPS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def get(self, **kwargs):
        """
        GET /domain/<domain_id>/groups Fetch all user_groups of a given domain

        :return A dictionary containing id and name of all user_groups of a given domain
        :rtype: dict
        """

        requested_domain_id = kwargs.get('domain_id')
        requested_domain = Domain.query.get(requested_domain_id)

        if not requested_domain:
            raise NotFoundError(error_message="Domain with domain_id %s doesn't exist" % requested_domain_id)

        if requested_domain_id != request.user.domain_id and not request.is_admin_user:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to get all user_groups "
                                                  "of domain %s" % (request.user.id, requested_domain_id))

        all_user_groups_of_domain = UserGroup.all_groups_of_domain(requested_domain_id)
        return {"user_groups": [{'id': user_group.id, 'name': user_group.name} for user_group in
                                all_user_groups_of_domain]}

    @require_any_role(DomainRole.Roles.CAN_ADD_DOMAIN_GROUPS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def post(self, **kwargs):
        """
        POST /domain/<domain_id>/groups Add user_groups to a given domain

        :return A dictionary containing ids of user_groups added to given domain
        :rtype: dict
        """

        requested_domain_id = kwargs.get('domain_id')
        requested_domain = Domain.query.get(requested_domain_id)

        if not requested_domain:
            raise NotFoundError(error_message="Domain with domain_id %s doesn't exist" % requested_domain_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'groups' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_domain_id != request.user.domain_id and not request.is_admin_user:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to add user_groups "
                                                  "to domain %s" % (request.user.id, requested_domain_id))

        user_groups = UserGroup.add_groups(posted_data.get('groups'), requested_domain_id)
        return {'user_groups': [user_group.id for user_group in user_groups]}

    @require_any_role(DomainRole.Roles.CAN_EDIT_DOMAIN_GROUPS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def put(self, **kwargs):
        """
        PUT /domain/groups/<group_id> Edit a user group with given group_id

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_group_id = kwargs.get('group_id')
        requested_group = UserGroup.query.get(requested_group_id)

        if not requested_group:
            raise NotFoundError(error_message="User Group with id %s doesn't exist" % requested_group_id)

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_group.domain_id != request.user.domain_id and not request.is_admin_user:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to edit user_groups %s"
                                                  % (request.user.id, requested_group.name))

        name = posted_data.get('name')
        description = posted_data.get('description')

        if not name and not description:
            raise InvalidUsage(error_message="Neither name nor description is provided")

        if name and not UserGroup.query.filter_by(name=name, domain_id=requested_group.domain_id).all():
            requested_group.name = name
        elif name:
            raise InvalidUsage(error_message="User group '%s' already exists in domain %s" % (name, requested_group.domain_id))

        if description:
            requested_group.description = description

        db.session.commit()
        return {"success_message": "User group has been updated successfully"}

    @require_any_role(DomainRole.Roles.CAN_DELETE_DOMAIN_GROUPS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def delete(self, **kwargs):
        """
        DELETE /domain/<domain_id>/groups Remove user_groups from a given domain

        :return A dictionary containing success message
        :rtype: dict
        """

        requested_domain_id = kwargs.get('domain_id')
        requested_domain = Domain.query.get(requested_domain_id)

        if not requested_domain:
            raise NotFoundError(error_message="Domain with domain_id %s doesn't exist" % requested_domain_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'groups' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_domain_id != request.user.domain_id and not request.is_admin_user:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to remove user_groups "
                                                  "from domain %s" % (request.user.id, requested_domain_id))

        UserGroup.delete_groups(requested_domain_id, posted_data.get('groups'))
        return {"success_message": "All given user_groups have been removed successfully from given domain"}


groups_and_roles_blueprint = Blueprint('groups_and_roles_api', __name__)
api = TalentApi(groups_and_roles_blueprint)
api.add_resource(UserScopedRolesApi, UserServiceApi.USER_ROLES)
api.add_resource(UserGroupsApi, UserServiceApi.USER_GROUPS)
api.add_resource(DomainGroupsApi, UserServiceApi.DOMAIN_GROUPS, UserServiceApi.DOMAIN_GROUPS_UPDATE)