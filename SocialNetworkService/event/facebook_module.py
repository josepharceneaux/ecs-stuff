
import requests
from datetime import datetime, timedelta
import facebook
from gt_common.gt_models.event import Event
from SocialNetworkService.event.base import EventBase

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
            print error.message
            # info_to_log = dict(error_message=error.message)
        #   log_exception(self.traceback_info,
        #                 "Couldn't get Facebook events. %(error_message)s"
        #                 % info_to_log)
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
                print error.message
                #TODO log exception
            #   info_to_log = dict(url=response['paging']['next'],
            #                       error_message=error.message)
            #   log_exception(self.traceback_info,
            #                 "Couldn't get data while paginating over "
            #                 "Facebook records. URL: %(url)s, %(error_message)s"
            #                 % info_to_log)
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
                # TODO log exception
                print error.message
            #   log_exception(self.traceback_info,
            #                 "Couldn't get events's organizer info(Facebook )."
            #                 " %(error_message)s"
            #                 % info_to_log)
                raise
        try:
            event = Event(
                vendorEventId=event['id'],
                eventTitle=event['name'],
                eventDescription=event.get('description', ''),
                socialNetworkId=self.social_network.id,
                userId=self.user.id,
                groupId=0,
                eventAddressLine1=location['street'] if location and location.has_key('street') else '',
                eventAddressLine2='',
                eventCity=location['city'].title() if location and location.has_key('city') else '',
                eventState='',
                eventZipCode=location['zip'] if location and location.has_key('zip') else '',
                eventCountry=location['country'].title() if location and location.has_key('country') else '',
                eventLongitude=float(location['longitude']) if location and location.has_key('longitude') else 0,
                eventLatitude=float(location['latitude']) if location and location.has_key('latitude') else 0,
                eventStartDatetime=event['start_time'] if event and event.has_key('start_time') else None,
                eventEndDatetime=event['end_time'] if event and event.has_key('end_time') else None,
                organizerName=owner['name'] if owner and owner.has_key('name') else '',
                organizerEmail=organizer['email'] if organizer and organizer.has_key('email') else '',
                aboutEventOrganizer='',
                registrationInstruction='',
                eventCost='',
                eventCurrency='',
                maxAttendees=event['attending_count'] + event['maybe_count'] + event['noreply_count'] if (event and \
                    event.has_key('attending_count') and event.has_key('maybe_count') and event.has_key('noreply_count'))\
                else ''
            )
        except Exception as e:
            print e.message
            #log_exception(self.traceback_info,
            #             "Couldn't normalize event. "
            #             "eventName: %(name)s, "
            #             "eventId on Vendor:%(id)s, "
            #             "error_message: %(error_message)s, "
            #             % event)
        else:
            return event

    def create_event(self):
        pass
