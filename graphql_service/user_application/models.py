import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType

from graphql_service.common.models.user import (
    User as UserModel, Domain as DomainModel, UserGroup as UserGroupModel,
    Role as RoleModel, Permission as PermissionModel, PermissionsOfRole as
    PermissionsOfRoleModel)


class User(SQLAlchemyObjectType):

    class Meta:
        model = UserModel
        interfaces = (relay.Node,)

