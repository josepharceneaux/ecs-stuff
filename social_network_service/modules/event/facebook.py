"""
This modules contains Facebook class. It inherits from EventBase class.
Facebook contains methods to create, update, get, delete events.
It also contains methods to get RSVPs of events.
"""

# Standard Library
from datetime import datetime
from datetime import timedelta

# Third Party
import requests
# We have to import the Facebook page in the following way because we
# want to avoid name conflicts that arise due to name of the package and
# name of the files in which package is being used.
from social_network_service.social_network_app import logger
from social_network_service.modules.utilities import import_from_dist_packages

facebook = import_from_dist_packages('facebook')

# Application Specific
from social_network_service.common.models.venue import Venue
from social_network_service.common.models.event import Event
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.modules.event.base import EventBase


class Facebook(EventBase):
    """
    This class inherits from EventBase class.
    This implements the abstract methods defined in interface.

    :Example:

        To import Facebook event you have to do tha following:

        1. Create Facebook instance
            facebook_obj = Facebook(user=user_obj,
                            headers=authentication_headers)
        2. Then call process() of SocialNetworkBaseClass
            facebook_obj.process('event', user_credentials=user_credentials)

        What process() will do internally is given in the following steps:
            1- from social_network_service.event.facebook import Facebook
            facebook_event_obj = Facebook(user_credentials=user_credentials,
                                       social_network=self.social_network,
                                       headers=self.headers)
            events = facebook_event_obj.get_events()
    - See also process() in SocialNetworkBase class inside social_network_service/base.py
    """

    def __init__(self, *args, **kwargs):
        """
        This method initializes facebook object and assigns default/initial
        values.
        This object has following attributes:
            - events:
                a list of events from social network
            - rsvp:
                a list of RSVPs for events in 'events' list
            - data:
                a dictionary containing post request data to create event
            - user:
                User object  user who sent the request to create this object
            - user_credentials:
                user credentials for facebook for this user
            - social_network:
                SocialNetwork object representing Facebook SN
            - api_url:
                URL to access Facebook API
            - start_date:
                Start date  to import events (i.e. import events after this date (inclusive))
            - end_date:
                last date for importing events. (i.e. import events before this date (inclusive))
            - graph:
                GraphAPI object which will be used to get all data from facebook through its
                Graph API.

        :param args:
        :param kwargs:
        """
        super(Facebook, self).__init__(*args, **kwargs)
        self.start_date = (datetime.now() - timedelta(days=3000)).strftime("%Y-%m-%d")
        self.end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        self.graph = None

    def get_events(self):
        """
        This method retrieves events from facebook through its Graph API and
        saves in database.
        We send GET requests to API URL and get data. We also
        have to handle pagination because Facebook's API
        sends paginated response.
        :return: all events of getTalent user on Facebook within specified
            time range
        :rtype: list

            :Example:

                create facebook object and call get_events on it
                facebook = Facebook(user=gt_user,
                                    headers=auth_headers)
                facebook.get_events()
        """
        self.graph = facebook.GraphAPI(access_token=self.access_token)
        all_events = []
        user_events = []
        # https://developer.facebook.com to see detail on params
        try:
            response = self.graph.get_object(
                'v2.4/me/events',
                fields='is_viewer_admin, description, name, category, owner, '
                       'place, start_time, ticket_uri, end_time, parent_group, '
                       'attending_count, maybe_count, noreply_count, timezone',
                since=self.start_date,
                until=self.end_date
            )
        except facebook.GraphAPIError:
            logger.exception('get_events: user_id: %s' % self.user.id)
            raise
        if 'data' in response:
            user_events.extend(response['data'])
            self.get_all_pages(response, user_events)
        # Need only events user is an admin of
        user_events = filter(lambda event: event['is_viewer_admin'] is True,
                             user_events)
        all_events.extend(user_events)
        return all_events

    def get_all_pages(self, response, target_list):
        """
        We keep iterating over pages as long as keep finding the URL
        in response['paging']['next'].
        :param response:
        :param target_list:
        :type response: dict
        :type target_list: list
        """
        while True:
            try:
                response = requests.get(response['paging']['next'])
                if response.ok:
                    response = response.json()
                if response and response['data']:
                    target_list.extend(response['data'])
            except KeyError:
                break
            except requests.HTTPError:
                logger.exception('get_all_pages: user_id: %s' % self.user.id)
                raise

    def event_sn_to_gt_mapping(self, event):
        """
        We take event's data from social network's API and map its fields to
        getTalent database fields. Finally we return Event's object to
        save/update record in getTalent database.
        We also issue some calls to get updated venue and organizer information.
        :param event: data from Facebook API.
        :type event: dictionary
        :exception Exception: It raises exception if there is an error getting
            data from API.
        :return: event: Event object
        :rtype event: common.models.event.Event
        """
        venue = None
        location = None
        venue_id = None
        organizer = None
        organizer_id = None
        assert event is not None
        owner = event.get('owner')
        if event.get('place'):
            venue = event.get('place')
            location = venue['location']
            try:
                organizer = self.graph.get_object('v2.4/' + owner['id'])
                organizer = organizer.get('data')
            except facebook.GraphAPIError:
                logger.exception('event_sn_to_gt_mapping: Getting data of organizer. '
                                 'user_id: %s, social_network_event_id: %s'
                                 % (self.user.id, event['id']))
                raise
        if owner or organizer:
            organizer_data = dict(
                user_id=self.user.id,
                name=owner['name'] if owner and owner.has_key('name') else '',
                email=organizer['email'] if organizer and organizer.has_key(
                    'email') else '',
                about=''
            )
            organizer_in_db = EventOrganizer.get_by_user_id_and_name(
                self.user.id,
                owner['name'] if owner and owner.has_key('name') else '')

            if organizer_in_db:
                organizer_in_db.update(**organizer_data)
                organizer_id = organizer_in_db.id
            else:
                organizer_instance = EventOrganizer(**organizer_data)
                EventOrganizer.save(organizer_instance)
                organizer_id = organizer_instance.id

        if venue:
            venue_data = dict(
                social_network_venue_id=venue['id'],
                user_id=self.user.id,
                address_line_1=location['street'] if location.has_key(
                    'street') else '',
                address_line_2='',
                city=location['city'].title() if location.has_key(
                    'city') else '',
                state='',
                zip_code=location['zip'] if location.has_key('zip') else None,
                country=location['country'].title() if location.has_key(
                    'country') else '',
                longitude=float(location['longitude']) if location.has_key(
                    'longitude') else 0,
                latitude=float(location['latitude']) if location.has_key(
                    'latitude') else 0,
            )
            venue_in_db = Venue.get_by_user_id_and_social_network_venue_id(
                self.user.id,
                venue['id'])
            if venue_in_db:
                venue_in_db.update(**venue_data)
                venue_id = venue_in_db.id
            else:
                venue = Venue(**venue_data)
                Venue.save(venue)
                venue_id = venue.id
        try:
            event = Event(
                social_network_event_id=event['id'],
                title=event['name'],
                description=event.get('description', ''),
                social_network_id=self.social_network.id,
                user_id=self.user.id,
                organizer_id=organizer_id,
                venue_id=venue_id,
                social_network_group_id=0,
                start_datetime=event.get('start_time'),
                end_datetime=event.get('end_time'),
                timezone=event.get('timezone'),
                registration_instruction='',
                cost=0,
                currency='',
                max_attendees=event['attending_count'] + event['maybe_count']
                              + event['noreply_count']
                if (event
                    and event.has_key('attending_count')
                    and event.has_key('maybe_count')
                    and event.has_key('noreply_count'))
                else ''
            )
        except:
            logger.exception('event_sn_to_gt_mapping: user_id: %s, '
                             'social_network_event_id: %s' % (self.user.id, event['id']))
        else:
            return event

    def create_event(self):
        """
        Event creation via API is not allowed on Facebook but since it inherits
        EventBase class so we
        need to implement it
        :return:
        """
        pass

    def event_gt_to_sn_mapping(self, data):
        """
        Event creation via API is not allowed on Facebook.
        So there will be no mapping of fields.
        :return:
        """
        pass
