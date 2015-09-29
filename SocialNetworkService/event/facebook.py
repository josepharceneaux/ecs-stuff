import requests

from datetime import datetime, timedelta
from SocialNetworkService.utilities import get_message_to_log, log_exception, import_from_dist_packages
from gt_common.models.event import Event
from SocialNetworkService.event.base import EventBase

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
            # response = self.graph.get_object(
            #     'v2.4/1709562552598022/subscriptions',
            #     object='page',
            #     fields='conversations', verify_token='token',
            #     callback_url="http://localhost:8000/web/user/profile",
            #     access_token='1709562552598022|R1S2eC2Btr9f06yiv3uOk4V2gx',
            #
            # )
        except facebook.GraphAPIError as error:
            message_to_log = get_message_to_log(function_name='get_events',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=error.message,
                                                file_name=__file__)
            log_exception(message_to_log)
            raise
        if 'data' in response:
            user_events.extend(response['data'])
            self.get_all_pages(response, user_events)
        # Need only events user is an admin of
        user_events = filter(lambda event: event['is_viewer_admin'] is True, user_events)
        all_events.extend(user_events)
        return all_events

    def get_all_pages(self, response, target_list):
        # self.traceback_info.update({"functionName": "get_all_pages()"})
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
                message_to_log = get_message_to_log(function_name='get_all_pages',
                                                    class_name=self.__class__.__name__,
                                                    gt_user=self.user.name,
                                                    error=error.message,
                                                    file_name=__file__)
                log_exception(message_to_log)
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
                message_to_log = get_message_to_log(function_name='normalize_event',
                                                    class_name=self.__class__.__name__,
                                                    gt_user=self.user.name,
                                                    error=error.message,
                                                    file_name=__file__)
                log_exception(message_to_log)
                raise
        try:
            event = Event(
                vendor_event_id=event['id'],
                event_title=event['name'],
                event_description=event.get('description', ''),
                social_network_id=self.social_network.id,
                user_id=self.user.id,
                group_id=0,
                event_address_line_1=location['street'] if location and location.has_key('street') else '',
                event_address_line_2='',
                event_city=location['city'].title() if location and location.has_key('city') else '',
                event_state='',
                event_zipcode=location['zip'] if location and location.has_key('zip') else '',
                event_country=location['country'].title() if location and location.has_key('country') else '',
                event_longitude=float(location['longitude']) if location and location.has_key('longitude') else 0,
                event_latitude=float(location['latitude']) if location and location.has_key('latitude') else 0,
                event_start_datetime=event['start_time'] if event and event.has_key('start_time') else None,
                event_end_datetime=event['end_time'] if event and event.has_key('end_time') else None,
                organizer_name=owner['name'] if owner and owner.has_key('name') else '',
                organizer_email=organizer['email'] if organizer and organizer.has_key('email') else '',
                about_event_organizer='',
                registration_instruction='',
                event_cost='',
                event_currency='',
                max_attendees=event['attending_count'] + event['maybe_count'] + event['noreply_count'] if (event and \
                    event.has_key('attending_count') and event.has_key('maybe_count') and event.has_key('noreply_count'))\
                else ''
            )
        except Exception as e:
            message_to_log = get_message_to_log(function_name='normalize_event',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=e.message,
                                                file_name=__file__)
            log_exception(message_to_log)
        else:
            return event

    def create_event(self):
        pass
