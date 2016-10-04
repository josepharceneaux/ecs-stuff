from ..models.venue import Venue
from ..models.user import User, Role, Permission, PermissionsOfRole
from ..models.event import Event
from ..models.event_organizer import EventOrganizer
from ..models.candidate import SocialNetwork

import graphene
from graphene import ObjectType
from graphene_sqlalchemy import SQLAlchemyObjectType


class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User


class PermissionsOfRoleType(SQLAlchemyObjectType):
    class Meta:
        model = PermissionsOfRole


class PermissionType(SQLAlchemyObjectType):
    class Meta:
        model = Permission


class RoleType(SQLAlchemyObjectType):
    class Meta:
        model = Role
    permissions = graphene.List(PermissionType)


class EventType(SQLAlchemyObjectType):
    class Meta:
        model = Event


class EventOrganizerType(SQLAlchemyObjectType):
    class Meta:
        model = EventOrganizer


class VenueType(SQLAlchemyObjectType):
    class Meta:
        model = Venue


class SocialNetworkType(SQLAlchemyObjectType):
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

