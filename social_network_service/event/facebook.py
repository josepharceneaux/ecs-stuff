import requests

from datetime import datetime, timedelta
from social_network_service.utilities import log_exception, import_from_dist_packages
from common.models.event import Event
from common.models.organizer import Organizer
from common.models.venue import Venue
from social_network_service.event.base import EventBase

# We have to import the Facebook page in the following way because we
# want to avoid name conflicts that arise due to name of the package and
# name of the files in which package is being used.
facebook = import_from_dist_packages('facebook')


class Facebook(EventBase):
    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)
        self.start_date = (datetime.now() - timedelta(days=3000)).strftime("%Y-%m-%d")
        self.end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.graph = None

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Facebook's API
        does that too.
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
        except facebook.GraphAPIError as error:
            log_exception({'user_id': self.user.id,
                           'error': error.message})
            raise
        if 'data' in response:
            user_events.extend(response['data'])
            self.get_all_pages(response, user_events)
        # Need only events user is an admin of
        user_events = filter(lambda event: event['is_viewer_admin'] is True, user_events)
        all_events.extend(user_events)
        return all_events

    def get_all_pages(self, response, target_list):
        """
        We keep iterating over pages as long as keep finding the URL
        in response['paging']['next'], when we don't we stop.
        :param response:
        :param target_list:
        :return:
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
            except requests.HTTPError as error:
                log_exception({'user_id': self.user.id,
                               'error': error.message})
                raise

    def event_sn_to_gt_mapping(self, event):
        """
        Basically we take event's data from Facebook's end
        and map their fields to getTalent db and finally we return
        Event's object (instance of SQLAlchemy model).
        TODO; document like Sphinx
        :param event:
        :return:
        """
        venue = None
        owner = None
        location = None
        venue_id = None
        organizer = None
        organizer_id = None
        assert event is not None
        if event.get('place'):
            venue = event.get('place')
            owner = event.get('owner')
            location = venue['location']
            try:
                organizer = self.graph.get_object('v2.4/' + owner['id'])
                organizer = organizer.get('data')
            except facebook.GraphAPIError as error:
                log_exception({'user_id': self.user.id,
                               'error': error.message})
                raise
        if owner or organizer:
            organizer_data = dict(
                user_id=self.user.id,
                name=owner['name'] if owner and owner.has_key('name') else '',
                email=organizer['email'] if organizer and organizer.has_key('email') else '',
                about=''
            )
            organizer_in_db = Organizer.get_by_user_id_and_name(
                self.user.id,
                owner['name'] if owner and owner.has_key('name') else '')

            if organizer_in_db:
                organizer_in_db.update(**organizer_data)
                organizer_id = organizer_in_db.id
            else:
                organizer_instance = Organizer(**organizer_data)
                Organizer.save(organizer_instance)
                organizer_id = organizer_instance.id

        if venue:
            venue_data = dict(
                social_network_venue_id=venue['id'],
                user_id=self.user.id,
                address_line1=location['street'] if location.has_key('street') else '',
                address_line2='',
                city=location['city'].title() if location.has_key('city') else '',
                state='',
                zipcode=location['zip'] if location.has_key('zip') else None,
                country=location['country'].title() if location.has_key('country') else '',
                longitude=float(location['longitude']) if location.has_key('longitude') else 0,
                latitude=float(location['latitude']) if location.has_key('latitude') else 0,
            )
            venue_in_db = Venue.get_by_user_id_and_social_network_venue_id(self.user.id,
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
                group_id=0,
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
        except Exception as error:
            log_exception({'user_id': self.user.id,
                           'error': error.message})
        else:
            return event

    def create_event(self):
        """
        Event creation via API is not alloewd on Facebook
        :return:
        """
        pass

    def event_gt_to_sn_mapping(self, data):
        """
        Event creation via API is not alloewd on Facebook.
        So ther will be no maapping of fields
        :return:
        """
        pass
