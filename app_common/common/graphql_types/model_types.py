"""
This module contains Graphene types for SqlAlchemy models. Instead of defining all our fields
manually for each and every model, we will make use of `SQLAlchemyObjectType` to easily create
our Graphene types from existing models.

In order to create a Graphene type of an SqlAlchemy model, simply create a class and inherit it from
`graphene_sqlalchemy.SQLAlchemyObjectType`. Add a nested `Meta` class with `user` attribute with value as
 SqlAlchemy model. e.g. for User model

 class UserType(SQLAlchemyObjectType):

    class Meta:
        model = User

By default, id field is being returned as string value like "1", "123" etc. so we need to explicitly define
`id` fields as Int field. so it will look like

class UserType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = User

:Authors:
    - Zohaib Ijaz    <mzohaib.qc@gmail.com>

"""
# 3rd party imports
import graphene
from graphene import ObjectType
from graphene_sqlalchemy import SQLAlchemyObjectType

# App specific imports
from ..models.event import Event
from ..models.venue import Venue
from ..models.candidate import SocialNetwork
from ..models.event_organizer import EventOrganizer
from ..models.user import User, Role, Permission, PermissionsOfRole


class UserType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = User


class PermissionsOfRoleType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = PermissionsOfRole


class PermissionType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = Permission


class RoleType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = Role
    permissions = graphene.List(PermissionType)


class EventType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = Event


class EventOrganizerType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = EventOrganizer


class VenueType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = Venue


class SocialNetworkType(SQLAlchemyObjectType):
    id = graphene.Int()

    class Meta:
        model = SocialNetwork


class MeetupGroupType(ObjectType):
    id = graphene.Int()
    name = graphene.String()
    urlname = graphene.String()


class TimeZoneType(ObjectType):
    name = graphene.String()
    value = graphene.String()


class SocialNetworkTokenStatusType(ObjectType):
    status = graphene.Boolean()
    name = graphene.String()
