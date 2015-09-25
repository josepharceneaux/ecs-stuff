"""
This class gets us events for Eventbrite within a 14 day time window.
It inherits from Base and overrides get_events() and normalize_event()
"""

import json
from datetime import datetime, timedelta
from base import Base, logger
from utilities import Attendee, log_exception, log_error
from gt_models.event import Event
from gt_models.social_network import SocialNetwork
from gt_models.user import UserCredentials


class Eventbrite(Base):
    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)
        # Eventbrite expects a UTC string
        self.start_date_in_utc = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.vendor = 'Eventbrite'
        self.webhook_id = None
        self.headers = None

    def get_user_credentials_by_webhook(self):
        """
        This gives the Owner user's data using following class variables
        webhook_id: is the id of webhook of the Get Talent user
        social_network_id: is the id of social network of Get Talent user
        """
        assert self.webhook_id is not None

        # getting social_network object
        social_network = SocialNetwork.get_by_name(self.vendor)
        # gets gt-user object
        user = UserCredentials.get_by_webhook_id_and_social_network(
            self.webhook_id, social_network.id)
        webhook = {'webhook_id': self.webhook_id}
        if user:
            return user
        else:
            logger.error("No User found in database corresponding to webhook id "
                         "%(webhook_id)s" % webhook)

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Eventbrite's API
        does that too.
        :return:
        """
        self.traceback_info.update({"functionName": "get_events()"})
        events_url = self.api_url + '/events/search/?token=' + self.auth_token
        params = {'user.id': self.member_id,
                  'date_created.range_start': self.start_date_in_utc
                  }
        all_events = []
        response = self.http_get(events_url, params=params)
        if response.ok:
            try:
                data = response.json()
                page_size = data['pagination']['page_size']
                total_records = data['pagination']['object_count']
                all_events.extend(data['events'])
                current_page = 1
                total_pages = total_records / page_size
                for page in range(1, total_pages):
                    params_copy = params.copy()
                    current_page += 1
                    params_copy['page'] = current_page
                    response = self.http_get(events_url, params_copy)
                    if response.ok:
                        data = response.json()
                    all_events.extend(data['events'])
                return all_events
            except Exception as e:
                log_exception(self.traceback_info, e.message)
        return all_events

    def normalize_event(self, event):
        """
        Basically we take event's data from Eventbrite's end
        and map their fields to ours and finally we return
        Event's object. We also issue some calls to get updated
        venue and organizer information.
        :param event:
        :return:
        """
        self.traceback_info.update({"functionName": "normalize_event()"})
        organizer = None
        organizer_email = None
        # Get information about event's venue
        event_info_to_log = {
            'name': event['name']['text'],
            'id': event['id']}
        if event['venue_id']:
            response = self.http_get(self.api_url +
                                     '/venues/' + event['venue_id'] +
                                     '/?token=' + self.auth_token)
            if response.ok:
                try:
                    venue = response.json()
                    # Now let's try to get the information about the event's organizer
                    if event['organizer_id']:
                        response = self.http_get(self.api_url +
                                                 '/organizers/' + event['organizer_id']
                                                 + '/?token=' + self.auth_token)
                        if response.ok:
                            organizer = json.loads(response.text)
                        if organizer:
                            response = self.http_get(self.api_url + '/users/'
                                                     + self.member_id
                                                     + '/?token=' + self.auth_token)
                            if response.ok:
                                organizer_info = json.loads(response.text)
                                organizer_email = organizer_info['emails'][0]['email']
                    event_db = Event(
                        vendorEventId=event['id'],
                        eventTitle=event['name']['text'],
                        eventDescription=event['description']['text'],
                        socialNetworkId=self.social_network_id,
                        userId=self.gt_user_id,
                        groupId=0,
                        groupUrlName='',
                        eventAddressLine1=venue['address']['address_1'],
                        eventAddressLine2=venue['address']['address_2'] if venue else '',
                        eventCity=venue['address']['city'],
                        eventState=venue['address']['region'],
                        eventZipCode='',
                        eventCountry=venue['address']['country'],
                        eventLongitude=float(venue['address']['longitude']),
                        eventLatitude=float(venue['address']['latitude']),
                        eventStartDateTime=event['start']['local'],
                        eventEndDateTime=event['end']['local'],
                        organizerName=organizer['name'] if organizer else '',
                        organizerEmail=organizer_email,
                        aboutEventOrganizer=organizer['description'] if organizer else '',
                        registrationInstruction='',
                        eventCost='',
                        eventCurrency=event['currency'],
                        eventTimeZone=event['start']['timezone'],
                        maxAttendees=event['capacity'])
                except Exception as e:
                    event_info_to_log['error_message'] = e.message
                    log_exception(self.traceback_info,
                                  "Couldn't normalize event. "
                                  "eventName: %(name)s, "
                                  "eventId on Vendor:%(id)s, "
                                  "error_message: %(error_message)s, "
                                  % event_info_to_log)
                else:
                    return event_db
        else:
            log_error(self.traceback_info,
                      "Couldn't normalize event because it has no Venue."
                      "eventName:%(name)s, eventId on Vendor:%(id)s, "
                      % event_info_to_log)

    def get_rsvps(self, event):
        pass

    def _process_rsvps(self):
        log_exception(self.traceback_info,
                      NotImplementedError("Eventbrite RSVPs are handled via webhook"))
        raise

    def get_attendee(self, rsvp):
        """
        Here Data about attendee is gathered by api_call to the vendor
        :param vendor_rsvp: contains the id of rsvp for (eventbrite) in dictionary format
        :return: attendee object which contains data of the attendee
        """
        self.traceback_info.update({"functionName": "get_attendee()"})
        url = self.api_url + "/orders/" + rsvp['rsvp_id']
        payload = {'token': self.auth_token}
        response = self.http_get(url, params=payload)
        if response.ok:
            try:
                data = response.json()
                created_datetime = datetime.strptime(data['created'][:19],
                                                     "%Y-%m-%dT%H:%M:%S")
                attendee = Attendee()
                attendee.first_name = data['first_name']
                attendee.full_name = data['name']
                attendee.last_name = data['last_name']
                attendee.added_time = created_datetime
                attendee.rsvp_status = 'yes' if data['status'] == 'placed' else data['status']
                attendee.email = data['email']
                attendee.vendor_rsvp_id = rsvp['rsvp_id']
                attendee.gt_user_id = self.gt_user_id
                attendee.social_network_id = self.social_network_id
                attendee.vendor_img_link = \
                    "<img class='pull-right'" \
                    " style='width:60px;height:30px' " \
                    "src='/web/static/images/activities/eventbrite_logo.png'/>"
                # get event_id
                vendor_event_id = data['event_id']
                assert vendor_event_id is not None
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.gt_user_id, self.social_network_id, vendor_event_id)
                assert event is not None
                attendee.event = event
                return attendee
            except Exception as e:
                log_exception(self.traceback_info, e.message)
                return None