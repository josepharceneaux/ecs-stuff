"""
This module contains GraphQL schema for social network service.
"""

from social_network_service.common.graphql_types.types import *
from social_network_service.modules.social_network.meetup import Meetup
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.utils.api_utils import get_paginated_list, DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from social_network_service.social_network_app.restful.v1_data import get_timezones
from social_network_service.social_network_app.restful.v1_social_networks import is_token_valid


class Query(ObjectType):
    name = 'Query'

    """
        me {
            first_name
            last_name
            domain_id

            role {
                id
                name
                permissions {
                    id
                    name
                }
            }

            events {
                title
                start_datetime
                end_datetime
                organizer {
                    id
                    name
                }
            }

        }
    """
    me = graphene.Field(
        UserType
    )

    """
        user (id: 123) {
            first_name
            last_name
            domain_id

            role {
                id
                name
                permissions {
                    id
                    name
                }
            }

            events {
                title
                start_datetime
                end_datetime
                organizer {
                    id
                    name
                }
            }

        }
    """
    user = graphene.Field(
        UserType,
        id=graphene.Int()
    )

    """
        event (id: 123) {
            title
            start_datetime
            end_datetime
            organizer {
                id
                name
            }
        }
    """
    event = graphene.Field(
        EventType,
        id=graphene.Int()
    )

    """
        events (page:1, perPage=10) {
            title
            start_datetime
            end_datetime
            organizer {
                id
                name
            }
        }
    """
    events = graphene.List(
        EventType,
        page=graphene.Int(),
        per_page=graphene.Int()
    )

    """
        venues {
            address_line_1
            address_line_2
            latitude
            longitude
            zip_code
            city
            country
        }
    """
    venues = graphene.List(
        VenueType
    )

    """
        venue(id: 123) {
            address_line_1
            address_line_2
        }
    """
    venue = graphene.Field(
        VenueType,
        id=graphene.Int()
    )
    """
        organizer(id: 123) {
            id
            name
            about
        }
    """
    organizer = graphene.Field(
        EventOrganizerType,
        id=graphene.Int()
    )

    """
        organizers {
            id
            name
            about
        }
    """
    organizers = graphene.List(
        EventOrganizerType
    )

    """
        social_network (name : Meetup) {
            id
            name
            url
        }
    """
    social_network = graphene.Field(
        SocialNetworkType,
        name=graphene.String()
    )

    """
        social_networks {
            id
            name
            url
        }
    """
    social_networks = graphene.List(
        SocialNetworkType
    )

    """
        subscribed_social_networks {
            id
            name
            url
        }
    """
    subscribed_social_networks = graphene.List(
        SocialNetworkType
    )

    """
        meetup_groups {
            id
            name
            urlname
        }
    """
    meetup_groups = graphene.List(
        MeetupGroupType
    )

    """
        timezones {
            name
            value
        }
    """
    timezones = graphene.List(
        TimeZoneType
    )

    """
        sn_token_status (id: 123) {
            status
        }
    """
    sn_token_status = graphene.Field(
        SocialNetworkTokenStatusType,
        id=graphene.Int()
    )

    # ####################################### Resolvers ##########################################

    def resolve_me(self, args, request, info):
        """
        Resolves current user object
        """
        return User.get(request.user.id)

    def resolve_user(self, args, request, info):
        """
        Resolve a user object specified by id (if user belongs to current user's domain)
        """
        user_id = args.get('id')
        user = User.get(user_id)
        return user if user.domain_id == request.user.domain_id else None

    def resolve_event(self, args, request, info):
        """
        Resolves an event owned by current user.
        """
        event_id = args.get('id')
        return Event.get_by_user_and_event_id(request.user.id, event_id)

    def resolve_events(self, args, request, info):
        """
        Resolves current user's events specified by page number and per page args.
        """
        page = args.get('page', DEFAULT_PAGE)
        per_page = args.get('per_page', DEFAULT_PAGE_SIZE)
        events = request.user.events.order_by(Event.start_datetime.desc())
        return get_paginated_list(events, page, per_page).items

    def resolve_venue(self, args, request, info):
        """
        Resolves current user's created venue specified by id.
        """
        venue_id = args.get('id')
        venue = Venue.get_by_user_id_venue_id(request.user.id, venue_id)
        return venue

    def resolve_venues(self, args, request, info):
        """
        Resolves current user's created all venues.
        """
        venues = request.user.venues.all()
        return venues

    def resolve_organizer(self, args, request, info):
        """
        Resolves current user's created organizer object specified by given id.
        """
        organizer_id = args.get('id')
        event_organizer = EventOrganizer.get_by_user_id_organizer_id(request.user.id, organizer_id)
        return event_organizer

    def resolve_organizers(self, args, request, info):
        """
        Resolves current user's created all organizers.
        """
        event_organizers = request.user.event_organizers.all()
        return event_organizers

    def resolve_social_network(self, args, request, info):
        """
        Resolves social networks in gt database based on name
        """
        name = args.get('name')
        return SocialNetwork.get_by_name(name)

    def resolve_social_networks(self, args, request, info):
        """
        Resolves all social networks in gt database.
        """
        return SocialNetwork.get_all()

    def resolve_subscribed_social_networks(self, args, request, info):
        """
        Resolves social networks that user has subscribed.
        """
        return SocialNetwork.get_subscribed_social_networks(request.user.id)

    def resolve_meetup_groups(self, args, request, info):
        """
        Resolves current user's Meetup groups.
        """
        user_id = request.user.id
        try:
            meetup = Meetup(user_id=user_id)
            groups = meetup.get_groups()
        except Exception as e:
            raise InternalServerError(e.message)
        keys = ('id', 'name', 'urlname')
        return [MeetupGroupType(**{k: v for k, v in group.iteritems() if k in keys
                                   }) for group in groups]

    def resolve_timezones(self, args, request, info):
        """
        Resolves to a list of all timezones.
        """
        return [TimeZoneType(**timezone) for timezone in get_timezones()]

    def resolve_sn_token_status(self, args, request, info):
        """
        Resolves current user's token status for a specified social network, e.g. token validity for Eventbrite
        """
        _id = args.get('id')
        status, name = is_token_valid(_id, request.user.id)
        return SocialNetworkTokenStatusType(status=status, name=name)


schema = graphene.Schema(query=Query, auto_camelcase=False)
