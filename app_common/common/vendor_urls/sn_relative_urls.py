"""
This file contains URLs of different vendors e.g. Meetup, Eventbrite for social-network-service
"""


__author__ = 'basit'


class SocialNetworkUrls(object):
    """
    Here we have URLs for different vendors used in social-network-service
    """
    VALIDATE_TOKEN = 'validate_token'
    REFRESH_TOKEN = 'refresh_token'
    GROUPS = 'groups'
    VENUES = 'venues'
    VENUE = 'venue'
    EVENTS = 'events'
    EVENT = 'event'
    RSVPS = 'rsvps'
    ORDER = 'order'
    ORGANIZERS = 'organizers'
    ORGANIZER = 'organizer'
    TICKETS = 'tickets'
    PUBLISH_EVENT = 'publish_event'
    UNPUBLISH_EVENT = 'unpublish_event'
    USER = 'user'

    """ Social-Networks """
    MEETUP = {VALIDATE_TOKEN: '{}/member/self',
              REFRESH_TOKEN: '{}/access',
              GROUPS: '{}/groups',
              VENUES: '{}/venues',
              EVENTS: '{}/events',
              EVENT: '{}/event/{}',
              RSVPS: '{}/rsvps',
              }

    EVENTBRITE = {
        VALIDATE_TOKEN: '{}/users/me/',
        VENUES: '{}/venues/',
        VENUE: '{}/venues/{}',
        EVENTS: '{}/events/',
        EVENT: '{}/events/{}',
        RSVPS: '{}/events/{}/attendees',
        ORGANIZERS: '{}/organizers/',
        ORGANIZER: '{}/organizers/{}',
        TICKETS: '{}/events/{}/ticket_classes/',
        PUBLISH_EVENT: '{}/events/{}/publish/',
        UNPUBLISH_EVENT: '{}/events/{}/unpublish/',
        USER: '{}/users/{}',
        ORDER: '{}/orders/{}'
    }
