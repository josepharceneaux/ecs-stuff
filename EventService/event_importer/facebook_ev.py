"""
This class gets us events for Facebook within a given day time window.
It inherits from Base and overrides get_events() and normalize_event()
"""

import requests
from datetime import datetime, timedelta
from base import Base
import facebook
from utilities import Attendee, log_exception, log_error
from gt_models.event import Event


class Facebook(Base):
    """
    This class implements all functions required to import
    users' events from facebook and their RSVPs.
    """

    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)
        self.start_date = (datetime.now() - timedelta(days=3000)).strftime("%Y-%m-%d")
        self.end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.start_date_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        self.end_date_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        self.graph = None
        self.vendor = 'Facebook'

    def validate_token(self):
        url = self.api_url + '/me'
        headers = {'Authorization': 'Bearer %s' % self.user_credential.access_token}
        response = self.http_get(url, headers=headers)
        if response.ok:
            return True
        return False

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
            info_to_log = dict(error_message=error.message)
            log_exception(self.traceback_info,
                          "Couldn't get Facebook events. %(error_message)s"
                          % info_to_log)
            raise
        if 'data' in response:
            user_events.extend(response['data'])
            self.get_all_pages(response, user_events)
        # Need only events user is an admin of
        user_events = filter(lambda event: event['is_viewer_admin'] is True, user_events)
        all_events.extend(user_events)
        return all_events

    def get_all_pages(self, response, target_list):
        self.traceback_info.update({"functionName": "get_all_pages()"})
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
                info_to_log = dict(url=response['paging']['next'],
                                   error_message=error.message)
                log_exception(self.traceback_info,
                              "Couldn't get data while paginating over "
                              "Facebook records. URL: %(url)s, %(error_message)s"
                              % info_to_log)
                raise

    def normalize_event(self, event):
        """
        Basically we take event's data from Facebook's end
        and map their fields to getTalent db and finally we return
        Event's object (instance of SQLAlchemy model).
        :param event:
        :return:
        """
        self.traceback_info.update({"functionName": "normalize_event()"})
        if event.get('place'):
            venue = event.get('place')
            owner = event.get('owner')
            try:
                organizer = self.graph.get_object('v2.4/' + owner['id'])
            except facebook.GraphAPIError as error:
                info_to_log = dict(error_message=error.message)
                log_exception(self.traceback_info,
                              "Couldn't get events's organizer info(Facebook )."
                              " %(error_message)s"
                              % info_to_log)
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
                event['error_message'] = e.message
                log_exception(self.traceback_info,
                              "Couldn't normalize event. "
                              "eventName: %(name)s, "
                              "eventId on Vendor:%(id)s, "
                              "error_message: %(error_message)s, "
                              % event)
            else:
                return event_db
        else:
            log_error(self.traceback_info,
                      "Couldn't normalize event because it has no Venue."
                      " eventName:%(name)s,"
                      " eventId on Vendor:%(id)s, " % event)

    def get_rsvps(self, event):
        """
        This method retrieves RSPVs for user's events on Facebook.
        """
        self.traceback_info.update({"functionName": "get_rsvps()"})
        rsvps = []
        try:
            self.graph = facebook.GraphAPI(access_token=self.access_token)
            url = 'v2.4/%s' % str(event.vendorEventId) + '/'
            # Get list of people surely attending
            confirm_attendees = self.graph.get_object(url + 'attending')
        except facebook.GraphAPIError as error:
            info_to_log = dict(error_message=error.message)
            log_exception(self.traceback_info,
                          "Couldn't get 'attending' RSVPs (Facebook). %(error_message)s"
                          % info_to_log)
            raise
        rsvps += confirm_attendees['data']

        self.get_all_pages(confirm_attendees, rsvps)
        # Get list of people who aren't certain
        try:
            expected_attendees = self.graph.get_object(url + 'maybe')
        except facebook.GraphAPIError as error:
            info_to_log = dict(error_message=error.message)
            log_exception(self.traceback_info,
                          "Couldn't get 'maybe' RSVPs (Facebook). %(error_message)s"
                          % info_to_log)
            raise
        rsvps += expected_attendees['data']
        self.get_all_pages(expected_attendees, rsvps)
        # Get list of people who declined
        try:
            declined_attendees = self.graph.get_object(url + 'declined')
        except facebook.GraphAPIError as error:
            info_to_log = dict(error_message=error.message)
            log_exception(self.traceback_info,
                          "Couldn't get 'Declined' RSVPs (Facebook). %(error_message)s"
                          % info_to_log)
            raise
        rsvps += declined_attendees['data']
        self.get_all_pages(declined_attendees, rsvps)
        for rsvp in rsvps:
            rsvp.update({'vendor_event_id': str(event.vendorEventId)})
        return rsvps

    def get_attendee(self, rsvp):
        """
        RSVP data returned from Facebook API looks like
        So we will get the member data and issue a member call to get more info
        about member so we can later save him as a candidate
        :param rsvp:
        :return:
        """
        self.traceback_info.update({"functionName": "get_attendee()"})
        try:
            data = self.graph.get_object('v2.4/' + rsvp['id'],
                                         fields='first_name, last_name, name, '
                                                'email, location, address, link, picture')
        except facebook.GraphAPIError as error:
            info_to_log = dict(error_message=error.message)
            log_exception(self.traceback_info,
                          "Couldn't get Facebook's attendee info. %(error_message)s"
                          % info_to_log)
            raise
        if 'location' in data:
            try:
                location = self.graph.get_object('v2.4/'
                                                 + data['location']['id'],
                                                 fields='location')
            except facebook.GraphAPIError as error:
                info_to_log = dict(error_message=error.message)
                log_exception(self.traceback_info,
                              " Couldn't get location info (Facebook). %(error_message)s"
                              % info_to_log)
                raise
            if 'location' in location:
                location = location['location']
        else:
            location = {}
        if data:
            try:
                attendee = Attendee()
                attendee.first_name = data.get('first_name', '')
                attendee.last_name = data.get('last_name', '')
                attendee.full_name = data.get('name', '')
                attendee.email = data.get('email', '')
                attendee.city = location.get('city', '')
                attendee.country = location.get('country', '')
                attendee.latitude = location.get('latitude')
                attendee.longitude = location.get('longitude')
                attendee.zip = location.get('zip')
                attendee.profile_url = data.get('link', '')
                attendee.picture_url = data['picture']['data']['url'] if 'picture' in data else ''
                attendee.gt_user_id = self.gt_user_id
                attendee.social_network_id = self.social_network_id
                attendee.vendor_rsvp_id = rsvp['id']  # we are using profile_id
                # here as we do not have any rsvp_id for this vendor
                attendee.added_time = ' '
                attendee.vendor_img_link = "<img class='pull-right' " \
                                           "style='width:60px;height:30px' " \
                                           "src='/web/static/images/activities/facebook_logo.png'/>"
                vendor_event_id = rsvp['vendor_event_id']
                if rsvp['rsvp_status'].strip() == 'attending' \
                        or rsvp['rsvp_status'].strip() == 'maybe':
                    attendee.rsvp_status = 'yes'
                else:
                    attendee.rsvp_status = 'no'
                assert vendor_event_id is not None
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.gt_user_id, self.social_network_id, vendor_event_id)
                assert event is not None
                attendee.event = event
                return attendee
            except Exception as e:
                log_exception(self.traceback_info, e.message)
                return None
