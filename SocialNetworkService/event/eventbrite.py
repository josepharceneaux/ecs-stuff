
import pytz
import json
from base import EventBase
from datetime import datetime
from datetime import timedelta
from gt_common.models.event import Event

from SocialNetworkService.custom_exections import EventNotCreated
from SocialNetworkService.custom_exections import TicketsNotCreated
from SocialNetworkService.custom_exections import EventNotPublished
from SocialNetworkService.custom_exections import EventNotUnpublished
from SocialNetworkService.custom_exections import EventInputMissing
from SocialNetworkService.custom_exections import EventLocationNotCreated

from SocialNetworkService.event.base import EventBase
from SocialNetworkService.utilities import log_error, logger, log_exception, http_request
from gt_common.models.event import Event

EVENTBRITE = 'Eventbrite'
# TODO: Will replace this ULR with actual webhook URL (Flask App)
WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'


class EventbriteEvent(EventBase):
    """
    This class is inherited from TalentEventBase class.
    This implements the abstract methods defined in interface.
    It also implements functions to create event on Eventbrite website.
    """
    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        super(EventbriteEvent, self).__init__(EVENTBRITE, *args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.event_payload = None
        self.vendor_event_id = None
        self.ticket_payload = None
        self.venue_payload = None
        self.message_to_log.update({'class_name': EVENTBRITE})
        self.start_date_in_utc = kwargs.get('start_date') or \
            (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Eventbrite's API
        does that too.
        :return:
        """
        events_url = self.api_url + '/events/search/'
        params = {'user.id': self.member_id,
                  'date_created.range_start': self.start_date_in_utc
                  }
        all_events = []
        response = http_request('GET', events_url, params=params,
                                headers=self.headers)
        if response.ok:
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
                response = http_request('GET', events_url, params=params_copy,
                                        headers=self.headers)
                if response.ok:
                    data = response.json()
                all_events.extend(data['events'])
            return all_events
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
        organizer = None
        organizer_email = None
        # Get information about event's venue
        if event['venue_id']:
            response = http_request('GET', self.api_url + '/venues/' + event['venue_id'],
                                    headers=self.headers)
            if response.ok:
                venue = response.json()
                # Now let's try to get the information about the event's organizer
                if event['organizer_id']:
                    response = http_request('GET', self.api_url +
                                             '/organizers/' + event['organizer_id'],
                                            headers=self.headers)
                    if response.ok:
                        organizer = json.loads(response.text)
                    if organizer:
                        response = http_request('GET', self.api_url + '/users/'
                                                 + self.member_id,
                                                headers=self.headers)
                        if response.ok:
                            organizer_info = json.loads(response.text)
                            organizer_email = organizer_info['emails'][0]['email']
                event_db = Event(
                    vendor_event_id=event['id'],
                    event_title=event['name']['text'],
                    event_description=event['description']['text'],
                    social_network_id=self.social_network.id,
                    user_id=self.user.id,
                    group_id=0,
                    group_url_name='',
                    event_address_line_1=venue['address']['address_1'],
                    event_address_line_2=venue['address']['address_2'] if venue else '',
                    event_city=venue['address']['city'],
                    event_state=venue['address']['region'],
                    event_zipcode='',
                    event_country=venue['address']['country'],
                    event_longitude=float(venue['address']['longitude']),
                    event_latitude=float(venue['address']['latitude']),
                    event_start_datetime=event['start']['local'],
                    event_end_datetime=event['end']['local'],
                    organizer_name=organizer['name'] if organizer else '',
                    organizer_email=organizer_email,
                    about_event_organizer=organizer['description'] if organizer else '',
                    registration_instruction='',
                    event_cost='',
                    event_currency=event['currency'],
                    event_timezone=event['start']['timezone'],
                    max_attendees=event['capacity'])
                return event_db
        else:
            # TODO log exception here
            pass # log exception
    def create_event(self):
        """
        This function is used to post event on eventbrite.
        It uses helper functions create_event_tickets(), event_publish().
        If event is published successfully, returns True
        :return:
        """
        self.message_to_log.update({'functionName': 'create_event()'})
        venue_id = None
        # create url to post event
        if self.vendor_event_id is not None:  # updating event
            event_is_new = False
            url = self.api_url + "/events/" + self.vendor_event_id + '/'
            # need to fetch venue_id of provided event so that Venue can be updated
            response = http_request('POST', url, params=self.event_payload, headers=self.headers)
            if response.ok:
                venue_id = response.json()['venue_id']
        else:  # creating event
            url = self.api_url + "/events/"
            event_is_new = True
        venue_id = self.add_location(venue_id=venue_id)  # adding venue for the event
        self.event_payload['event.venue_id'] = venue_id
        response = http_request('POST', url, params=self.event_payload, headers=self.headers)
        if response.ok:  # event has been created on vendor and saved in draft there
            event_id = response.json()['id']
            # Ticket are going to be created/updated
            ticket_id = self.manage_event_tickets(event_id, event_is_new)
            if event_is_new:
                # Ticket(s) have been created for new created Event
                self.publish_event(event_id)
            else:
                logger.info("|  Event is already published  |")
            create_update = 'Created' if not self.vendor_event_id else 'Updated'
            logger.info('|  Event %s %s Successfully  |'
                        % (self.event_payload['event.name.html'],
                           create_update))
            return event_id, ticket_id
        else:
            error_message = 'Event was not created Successfully as draft'
            response = response.json()
            error_detail = response.get('error', '') + ': ' + response.get('error_description', '')
            if error_detail != ': ':
                error_message += '\n%s' % error_detail
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)
            raise EventNotCreated(error_message)

    def delete_event(self, event_id):
        event = Event.get_by_user_and_event_id(self.user_id, event_id)
        if event:
            try:
                self.unpublish_event(event_id)
                Event.delete(event_id)
                return True
            except:     # some error while removing event
                return False
        return False    # event not found in database

    def add_location(self, venue_id=None):
        """
        This generates/updates a venue object for the event and returns the
        id of venue.
        :param venue_id:
        :return:
        """
        self.message_to_log.update({'functionName': 'add_location()'})
        if venue_id:  # update event address
            url = self.api_url + "/venues/" + venue_id + "/"
            payload = self.venue_payload
            status = 'Updated'
            # Region gives error of region while updating venue, so removing
            payload.pop('venue.address.region')
        else:  # create venue for event
            url = self.api_url + "/venues/"
            status = 'Added'
        response = http_request('POST', url, params=self.venue_payload, headers=self.headers)
        if response.ok:
            logger.info('|  Venue has been %s  |' % status)
            return response.json().get('id')
        else:
            error_message = "Venue was not Created. There are some errors: " \
                            "Details: %s " % response
            message = '\nErrors from the vendor:\n'
            message += ''.join(response.json().get('error') + ',' + response.json().get('error_description'))
            error_message += message
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)
            raise EventLocationNotCreated('ApiError: Unable to create venue for event\n %s' % message)

    def manage_event_tickets(self, event_id, event_is_new):
        """
        Here tickets are created for event on Eventbrite.
        :param event_id:id of newly created event
        :param event_is_new: Status of new/old event
        :return: tickets_id
        """
        self.message_to_log.update({'functionName': 'manage_event_tickets()'})
        tickets_url = self.api_url + "/events/" + event_id + "/ticket_classes/"
        if not event_is_new:
            event = Event.get_by_user_and_vendor_id(self.user_id, event_id)
            if event.ticketsId:
                tickets_url = tickets_url + str(event.ticketsId) + '/'
            else:
                logger.info('Tickets ID is not available for event with id %s, %s'
                            % (event_id, self.message_to_log))
        response = http_request('POST', tickets_url, params=self.ticket_payload, headers=self.headers)
        if response.ok:
            logger.info('|  %s Ticket(s) have been created  |'
                        % str(self.ticket_payload['ticket_class.quantity_total']))
            return response.json().get('id')
        else:
            error_message = 'Tickets were not created successfully'
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)
            raise TicketsNotCreated('ApiError: Unable to create event tickets on Eventbrite')

    def publish_event(self, event_id):
        """
        This function publishes the Event on Eventbrite.
        :param event_id:
        :return:
        """
        self.message_to_log.update({'functionName': 'publish_event()'})
        # create url to publish event
        url = self.api_url + "/events/" + event_id + "/publish/"
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers)
        if response.ok:
            logger.info('|  Event has been published  |')
        else:
            error_message = "Event was not Published. There are some errors: " \
                            "Details: %s  |" % response
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)
            raise EventNotPublished('ApiError: Unable to publish event on specified social network')

    def unpublish_event(self, event_id):
        """
        This function is used to un publish the event from website of
        Eventbrite.
        :param event_id:
        :return:
        """
        self.message_to_log.update({'functionName': 'unpublish_event()'})
        # create url to publish event
        url = self.api_url + "/events/" + event_id + "/unpublish/"
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers)
        if response.ok:
            logger.info('|  Event has been unpublished  |')
        else:
            error_message = "Event was not unpublished. There are some errors. " \
                            "Response is %s  |" % response
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)
            raise EventNotUnpublished('ApiError: Unable to remove event from specified social network')

    def validate_required_fields(self, data):
        """
        Here we validate that all the required fields for the event creation on
        Eventbrite are filled. If any required filed is missing, raises exception
        named  EventInputMissing.
        """
        mandatory_input_data = ['eventTitle', 'eventDescription', 'eventEndDatetime',
                                'eventTimeZone', 'eventStartDatetime', 'eventCurrency']
        if not all([input in data and data[input] for input in mandatory_input_data]):
            raise EventInputMissing("Mandatory parameter missing in Eventbrite data.")

    def gt_to_sn_fields_mappings(self, data):
        """
        This is actually the mapping of data from the input data from
        EventCreationForm to the data required for API calls on Eventbrite.
        """
        self.message_to_log.update({'functionName': 'gt_to_sn_fields_mappings()'})
        if data:
            self.validate_required_fields(data)
            #  filling required fields for Eventbrite
            event_name = data['eventTitle']
            description = data['eventDescription']
            # Eventbrite assumes that provided start and end DateTime is in UTC
            # So, form given Timezone, (eventTimeZone in our case), It changes the
            # provided DateTime accordingly.
            # Here we are converting DateTime into UTC format to be sent to vendor
            utc_dts = []
            start_time = end_time = ''
            naive_dts = [data['eventStartDatetime'], data['eventEndDatetime']]
            if data['eventTimeZone']:
                local_timezone = pytz.timezone(data['eventTimeZone'])
                for naive_dt in naive_dts:
                    local_dt = local_timezone.localize(naive_dt, is_dst=None)
                    utc_dt = local_dt.astimezone(pytz.utc)
                    utc_dts.append(utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
                start_time = utc_dts[0]
                end_time = utc_dts[1]
            else:
                error_message = 'Time Zone is None for Event %s ' % event_name
                self.message_to_log.update({'error': error_message})
                log_error(self.message_to_log)
            currency = data['eventCurrency']
            time_zone = data['eventTimeZone']

            # Creating ticket data as Eventbrite wants us to associate tickets
            # with events
            venue_name = 'Event Address'
            number_of_tickets = data['maxAttendees']
            free_tickets = True
            ticket_type = 'Event Ticket'

            # This dict is used to create an event as a draft on vendor
            self.event_payload = {
                'event.start.utc': start_time,
                'event.start.timezone': time_zone,
                'event.end.utc': end_time,
                'event.end.timezone': time_zone,
                'event.currency': currency,
                'event.name.html': event_name,
                'event.description.html': description
            }

            # This dict is used to create venue for a specified event
            self.venue_payload = {
                'venue.name': venue_name,
                'venue.address.address_1': data['eventAddressLine1'],
                'venue.address.address_2': data['eventAddressLine2'],
                'venue.address.region': data['eventState'],
                'venue.address.city': data['eventCity'],
                # 'venue.address.country': data['eventCountry'],
                'venue.address.postal_code': data['eventZipCode'],
                'venue.address.latitude': data['eventLatitude'],
                'venue.address.longitude': data['eventLongitude'],
            }
            # This dict is used to create tickets for a specified event
            self.ticket_payload = {
                'ticket_class.name': ticket_type,
                'ticket_class.quantity_total': number_of_tickets,
                'ticket_class.free': free_tickets,
            }
            self.vendor_event_id = data.get('vendorEventId')
        else:
            error_message = 'Data is None'
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)

    def create_webhook(self, user_credentials):
        """
        Creates a webhook to stream the live feed of Eventbrite users to the
        Flask app. It gets called in the save_token_in_db().
        It takes user_credentials to save webhook against that user.
        Here it performs a check which ensures  that webhook is not generated
        every time code passes through this flow once a webhook has been
        created for a user (since webhooks don't expire and are unique for
        every user).
        :return: True if webhook creation is successful o/w False
        """
        self.message_to_log.update({'functionName': 'create_webhook()'})
        status = False
        if (user_credentials.userId == user_credentials.userId) \
                and (user_credentials.socialNetworkId == user_credentials.socialNetworkId) \
                and (user_credentials.webhook in [None, '']):
            url = self.api_url + "/webhooks/"
            payload = {'endpoint_url': WEBHOOK_REDIRECT_URL}
            response = http_request('POST', url, params=payload, headers=self.headers)
            if response.ok:
                try:
                    webhook_id = response.json()['id']
                    user_credentials.update_record(webhook=webhook_id)
                    status = True
                except Exception as e:
                    error_message = e.message
                    self.message_to_log.update({'error': error_message})
                    log_exception(self.message_to_log)
            else:
                error_message = "Webhook was not created successfully."
                self.message_to_log.update({'error': error_message})
                log_error(self.message_to_log)
        else:
            # webhook has already been created for this user
            status = True
        return status
