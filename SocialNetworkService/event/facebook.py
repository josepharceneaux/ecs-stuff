import requests

from datetime import datetime, timedelta
from SocialNetworkService.utilities import get_message_to_log, log_exception, import_from_dist_packages
from gt_common.models.event import Event
from gt_common.models.organizer import Organizer
from gt_common.models.venue import Venue
from SocialNetworkService.event.base import EventBase

# We have to import the Facebook page in the following way because we
# want to avoid name conflicts that arise due to name of the package and
# name of the files in which package is being used.
facebook = import_from_dist_packages('facebook')


class FacebookEvent(EventBase):
    def __init__(self, *args, **kwargs):
        super(FacebookEvent, self).__init__(FacebookEvent, *args, **kwargs)
        self.start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.graph = None

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Facebook's API
        does that too.
        """
        # self.traceback_info.update({"functionName": "get_events()"})
        print 'Facebook dir', dir(facebook)
        self.graph = facebook.GraphAPI(access_token=self.access_token)
        all_events = []
        user_events = []
        # https://developer.facebook.com to see detail on params
        try:
            response = self.graph.get_object(
                'v2.4/me/events',
                fields='is_viewer_admin, description, name, category, owner, '
                       'place, start_time, ticket_uri, end_time, parent_group, '
                       'attending_count, maybe_count, noreply_count',
                since=self.start_date,
                until=self.end_date
            )
        except facebook.GraphAPIError as error:
            log_exception(
                dict(
                    functionName='get_events',
                    user=self.user.name,
                    error=error.message,
                    fileName=__file__
                )
            )
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
                log_exception(
                    dict(
                        function_name='get_all_pages',
                        class_name=self.__class__.__name__,
                        gt_user=self.user.name,
                        error=error.message,
                        file_name=__file__
                    )
                )
                raise

    def normalize_event(self, event):
        """
        Basically we take event's data from Facebook's end
        and map their fields to getTalent db and finally we return
        Event's object (instance of SQLAlchemy model).
        :param event:
        :return:
        """
        # self.traceback_info.update({"functionName": "normalize_event()"})
        venue = None
        venue_instance = None
        organizer_instance = None
        owner = None
        organizer = None
        location = None
        assert event is not None
        if event.get('place'):
            venue = event.get('place')
            owner = event.get('owner')
            location = venue['location']
            try:
                organizer = self.graph.get_object('v2.4/' + owner['id'])
                organizer = organizer.get('data')
            except facebook.GraphAPIError as error:
                log_exception({
                            'Reason': error.message,
                            'functionName': 'normalize_event',
                            'fileName': __file__,
                            'User': self.user.id
                        })
                raise
        if owner or organizer:
            organizer_instance = Organizer(
                user_id=self.user.id,
                name=owner['name'] if owner and owner.has_key('name') else '',
                email=organizer['email'] if organizer and organizer.has_key('email') else '',
                about=''

            )
            Organizer.save(organizer_instance)
        if location:
            venue_instance = Venue(
                social_network_venue_id=event['venue_id'],
                user_id=self.user.id,
                address_line1=location['street'] if location.has_key('street') else '',
                address_line2='',
                city=location['city'].title() if location.has_key('city') else '',
                state='',
                zipcode=location['zip'] if location.has_key('zip') else '',
                country=location['country'].title() if location.has_key('country') else '',
                longitude=float(location['longitude']) if location.has_key('longitude') else 0,
                latitude=float(location['latitude']) if location.has_key('latitude') else 0,
            )
            Venue.save(venue_instance)
        try:
            event = Event(
                social_network_event_id=event['id'],
                title=event['name'],
                description=event.get('description', ''),
                social_network_id=self.social_network.id,
                user_id=self.user.id,
                organizer_id=organizer_instance.id if organizer_instance else None,
                venue_id=venue_instance.id if venue_instance else None,
                group_id=0,
                start_datetime=event['start_time'] if event and event.has_key('start_time') else None,
                end_datetime=event['end_time'] if event and event.has_key('end_time') else None,
                about_event_organizer='',
                registration_instruction='',
                cost='',
                event_currency='',
                max_attendees=event['attending_count'] + event['maybe_count'] + event['noreply_count'] if (event and \
                    event.has_key('attending_count') and event.has_key('maybe_count') and event.has_key('noreply_count'))\
                else ''
            )
        except Exception as error:
            log_exception(
                dict(
                    function_name='normalize_event',
                    class_name=self.__class__.__name__,
                    gt_user=self.user.name,
                    error=error.message,
                    file_name=__file__
                )
            )
        else:
            return event

    def create_event(self):
        pass
