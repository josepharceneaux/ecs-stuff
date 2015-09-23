import requests
import facebook
from common.gt_models.event import Event
from base import EventBase


class Facebook(EventBase):

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Facebook's API
        does that too.
        """
        self.traceback_info.update({"functionName": "get_events()"})
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
            raise
        if 'data' in response:
            user_events.extend(response['data'])
            self.get_all_pages(response, user_events)
        # Need only events user is an admin of
        user_events = filter(lambda event: event['is_viewer_admin'] is True, user_events)
        all_events.extend(user_events)
        return all_events

    def get_all_pages(self, response, target_list):
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
                raise

    def normalize_event(self, event):
        """
        Basically we take event's data from Facebook's end
        and map their fields to getTalent db and finally we return
        Event's object (instance of SQLAlchemy model).
        :param event:
        :return:
        """
        if event.get('place'):
            venue = event.get('place')
            owner = event.get('owner')
            try:
                organizer = self.graph.get_object('v2.4/' + owner['id'])
            except facebook.GraphAPIError as error:
                raise
            organizer = organizer.get('data')
            location = venue['location']
            try:
                event_db = Event(
                    vendorEventId=event['id'],
                    eventTitle=event['name'],
                    eventDescription=event.get('description', ''),
                    socialNetworkId=self.social_network_id,
                    userId=self.gt_user_id,
                    groupId=0,
                    eventAddressLine1=location['street'],
                    eventAddressLine2='',
                    eventCity=location['city'].title(),
                    eventState='',
                    eventZipCode=location['zip'],
                    eventCountry=location['country'].title(),
                    eventLongitude=float(location['longitude']),
                    eventLatitude=float(location['latitude']),
                    eventStartDateTime=event['start_time'] if 'start_time' in event else None,
                    eventEndDateTime=event['end_time'] if event.has_key('end_time') else None,
                    organizerName=owner['name'] if owner and 'name' in owner else '',
                    organizerEmail=organizer['email'] if organizer else '',
                    aboutEventOrganizer='',
                    registrationInstruction='',
                    eventCost='',
                    eventCurrency='',
                    maxAttendees=event['attending_count'] + event['maybe_count'] + event['noreply_count']
                )
            except Exception as e:
                raise
            else:
                return event_db
        else:
            raise Exception("")