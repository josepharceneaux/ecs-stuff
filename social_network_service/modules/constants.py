"""
This file consists constants used in social-network-service
"""

__author__ = 'basit'

from social_network_service.common.constants import MEETUP

# URL to be hit in case of application based authentication
APPLICATION_BASED_AUTH_URL = 'https://api.twitter.com/oauth2/token'
MEETUP_EVENT_STREAM_API_URL = "http://stream.meetup.com/2/open_events?since_count=10"
MEETUP_RSVPS_STREAM_API_URL = "http://stream.meetup.com/2/rsvps?since_mtime=%s"
MEETUP_CODE_LENGTH = 32
QUEUE_NAME = 'social_network'
EVENTBRITE = 'eventbrite'
FACEBOOK = 'facebook'
TASK_ALREADY_SCHEDULED = 6057
EVENT = 'event'
RSVP = 'rsvp'

# API URL for Meetup venues
# For creating venue for event, Meetup uses url which is
# different than the url we use in other API calls of Meetup.
MEETUP_VENUE = 'https://api.meetup.com/{}'

# Vendors to be mocked goes here
MOCK_VENDORS = [MEETUP]
SORT_TYPES = ('asc', 'desc')
EVENTBRITE_USER_AGENT = 'Eventbrite Webhooks'
ACTIONS = {
    'created': 'event.created',
    'published': 'event.published',
    'updated': 'event.updated',
    'unpublished': 'event.unpublished'
}

MEETUP_EVENT_STATUS = {
    'upcoming': 'upcoming',
    'proposed': 'proposed',
    'suggested': 'suggested',
    'canceled': 'canceled',
    'deleted': 'deleted'
}

