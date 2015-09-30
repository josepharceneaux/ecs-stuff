
import pytz
import json
from datetime import datetime
from datetime import timedelta
from social_network_service.custom_exections import EventNotCreated
from social_network_service.custom_exections import TicketsNotCreated
from social_network_service.custom_exections import EventNotPublished
from social_network_service.custom_exections import EventNotUnpublished
from social_network_service.custom_exections import EventInputMissing
from social_network_service.custom_exections import EventLocationNotCreated
from gt_common.models.organizer import Organizer
from gt_common.models.venue import Venue
from social_network_service.event.base import EventBase
from social_network_service.utilities import log_error, logger, log_exception, \
    http_request, get_message_to_log
from gt_common.models.event import Event

EVENTBRITE = 'Eventbrite'
# TODO: Will replace this ULR with actual webhook URL (Flask App)
WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'


class Eventbrite(EventBase):
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
        super(Eventbrite, self).__init__(EVENTBRITE, *args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.event_payload = None
        self.social_network_event_id = None
        self.ticket_payload = None
        self.venue_payload = None
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
        try:
            response = http_request('GET', events_url, params=params,
                                headers=self.headers)
        except Exception as error:
            log_exception({
                            'Reason': error.message,
                            'functionName': 'get_events',
                            'fileName': __file__,
                            'User': self.user.id
                        })
            raise
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
                try:
                    response = http_request('GET', events_url, params=params_copy,
                                        headers=self.headers)
                except Exception as error:
                    log_exception({
                            'Reason': error.message,
                            'functionName': 'get_events',
                            'fileName': __file__,
                            'User': self.user.id
                        })
                    raise
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
        venue = None
        organizer_instance = None
        venue_instance = None
        assert event is not None

        # Get information about event's venue
        if event['venue_id']:
            try:
                response = http_request('GET', self.api_url + '/venues/' + event['venue_id'],
                                    headers=self.headers)
            except Exception as error:
                log_exception({
                            'Reason': error.message,
                            'functionName': 'normalize_event',
                            'fileName': __file__,
                            'User': self.user.id
                        })
                raise
            if response.ok:
                venue = response.json()
                # Now let's try to get the information about the event's organizer
                if event['organizer_id']:
                    try:
                        response = http_request('GET', self.api_url +
                                             '/organizers/' + event['organizer_id'],
                                            headers=self.headers)
                    except Exception as error:
                        log_exception({
                            'Reason': error.message,
                            'functionName': 'normalize_event',
                            'fileName': __file__,
                            'User': self.user.id
                        })
                        raise
                    if response.ok:
                        organizer = json.loads(response.text)
                    if organizer:
                        try:
                            response = http_request('GET', self.api_url + '/users/'
                                                 + self.member_id,
                                                headers=self.headers)
                        except Exception as error:
                            log_exception({
                                'Reason': error.message,
                                'functionName': 'normalize_event',
                                'fileName': __file__,
                                'User': self.user.id
                            })
                            raise
                        if response.ok:
                            organizer_info = json.loads(response.text)
                            organizer_email = organizer_info['emails'][0]['email']

        if organizer:
            organizer_instance = Organizer(
                user_id=self.user.id,
                name=organizer['name'] if organizer.has_key('name') else '',
                email=organizer_email if organizer_email else '',
                about=organizer['description'] if organizer.has_key('description') else ''

            )
            Organizer.save(organizer_instance)
        if venue:
            venue_instance = Venue(
                social_network_venue_id=event['venue_id'],
                user_id=self.user.id,
                address_line1=venue['address']['address_1'] if venue else '',
                address_line2=venue['address']['address_2'] if venue else '',
                city=venue['address']['city'] if venue else '',
                state=venue['address']['region'] if venue else '',
                zipcode='',
                country=venue['address']['country'] if venue else '',
                longitude=float(venue['address']['longitude']) if venue else 0,
                latitude=float(venue['address']['latitude']) if venue else 0,
            )
            Venue.save(venue_instance)

        return Event(
            social_network_event_id=event['id'],
            title=event['name']['text'],
            description=event['description']['text'],
            social_network_id=self.social_network.id,
            organizer_id = organizer_instance.id if organizer_instance else None,
            user_id=self.user.id,
            group_id=0,
            url='',
            group_url_name='',
            venue_id=venue_instance.id if venue_instance.id else None,
            start_datetime=event['start']['local'],
            end_datetime=event['end']['local'],
            registration_instruction='',
            cost=0,
            currency=event['currency'],
            timezone=event['start']['timezone'],
            max_attendees=event['capacity']
        )

    def create_event(self):
        """
        This function is used to post event on eventbrite.
        It uses helper functions create_event_tickets(), event_publish().
        If event is published successfully, returns True
        :return:
        """
        venue_id = None
        # create url to post event
        if self.social_network_event_id is not None:  # updating event
            event_is_new = False
            url = self.api_url + "/events/" + self.social_network_event_id + '/'
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
            create_update = 'Created' if not self.social_network_event_id else 'Updated'
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
            log_exception(
                dict(
                    functionName='create_event',
                    user=self.user.name,
                    error=error_detail,
                    fileName=__file__
                )
            )
            raise EventNotCreated(error_message)

    def delete_event(self, event_id):
        event = Event.get_by_user_and_event_id(self.user_id, event_id)
        if event:
            try:
                self.unpublish_event(event_id)
                Event.delete(event_id)
                return True
            except Exception as error:     # some error while removing event
                log_exception(
                    dict(
                        functionName='delete_event',
                        error=error.message,
                        user=self.user.name,
                        fileName=__file__
                    )
                )
                return False
        return False    # event not found in database

    def add_location(self, venue_id=None):
        """
        This generates/updates a venue object for the event and returns the
        id of venue.
        :param venue_id:
        :return:
        """
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
            log_error(
                dict(
                    error=error_message,
                    functionName='add_location',
                    fileName=__file__,
                    user=self.user.name
                )
            )
            raise EventLocationNotCreated('ApiError: Unable to create venue for event\n %s' % message)

    def manage_event_tickets(self, event_id, event_is_new):
        """
        Here tickets are created for event on Eventbrite.
        :param event_id:id of newly created event
        :param event_is_new: Status of new/old event
        :return: tickets_id
        """
        tickets_url = self.api_url + "/events/" + event_id + "/ticket_classes/"
        if not event_is_new:
            event = Event.get_by_user_and_vendor_id(self.user.id, event_id)
            if event.tickets_id:
                tickets_url = tickets_url + str(event.tickets_id) + '/'
            else:
                logger.info('Tickets ID is not available for event with id %s, User:  %s'
                            % (event_id, self.user.name))
        response = http_request('POST', tickets_url, params=self.ticket_payload, headers=self.headers)
        if response.ok:
            logger.info('|  %s Ticket(s) have been created  |'
                        % str(self.ticket_payload['ticket_class.quantity_total']))
            return response.json().get('id')
        else:
            log_error(
                dict(
                    error='Event tickets were not created successfully',
                    functionName='manage_event_tickets',
                    fileName=__file__,
                    user=self.user.name
                )
            )
            raise TicketsNotCreated('ApiError: Unable to create event tickets on Eventbrite')

    def publish_event(self, event_id):
        """
        This function publishes the Event on Eventbrite.
        :param event_id:
        :return:
        """
        # create url to publish event
        url = self.api_url + "/events/" + event_id + "/publish/"
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers)
        if response.ok:
            logger.info('|  Event has been published  |')
        else:
            error_message = "Event was not Published. There are some errors: " \
                            "Details: %s  |" % response
            log_error(
                dict(
                    error=error_message,
                    functionName='publish_event',
                    fileName=__file__,
                    user=self.user.name
                )
            )
            raise EventNotPublished('ApiError: Unable to publish event on specified social network')

    def unpublish_event(self, event_id):
        """
        This function is used to un publish the event from website of
        Eventbrite.
        :param event_id:
        :return:
        """
        # create url to publish event
        url = self.api_url + "/events/" + event_id + "/unpublish/"
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers)
        if response.ok:
            logger.info('|  Event has been unpublished  |')
        else:
            error_message = "Event was not unpublished. There are some errors. " \
                            "Response is %s  |" % response
            log_error(
                dict(
                    error=error_message,
                    functionName='unpublish_event',
                    fileName=__file__,
                    user=self.user.name
                )
            )
            raise EventNotUnpublished('ApiError: Unable to remove event from specified social network')

    @staticmethod
    def validate_required_fields(data):
        """
        Here we validate that all the required fields for the event creation on
        Eventbrite are filled. If any required filed is missing, raises exception
        named  EventInputMissing.
        """
        mandatory_input_data = ['title', 'description', 'end_datetime',
                                'timezone', 'start_datetime', 'currency']
        if not all([input in data and data[input] for input in mandatory_input_data]):
            log_error(
                dict(
                    error='Mandatory parameters missing in Eventbrite data',
                    functionName='validate_required_files',
                    fileName=__file__,
                    user=''
                )
            )
            raise EventInputMissing("Mandatory parameter missing in Eventbrite data.")

    def gt_to_sn_fields_mappings(self, data):
        """
        This is actually the mapping of data from the input data from
        EventCreationForm to the data required for API calls on Eventbrite.
        """
        if data:
            self.validate_required_fields(data)
            #  filling required fields for Eventbrite
            event_name = data['title']
            description = data['description']
            # Eventbrite assumes that provided start and end DateTime is in UTC
            # So, form given Timezone, (eventTimeZone in our case), It changes the
            # provided DateTime accordingly.
            # Here we are converting DateTime into UTC format to be sent to vendor
            utc_dts = []
            start_time = end_time = ''
            naive_dts = [data['start_datetime'], data['start_datetime']]
            if data['timezone']:
                local_timezone = pytz.timezone(data['timezone'])
                for naive_dt in naive_dts:
                    local_dt = local_timezone.localize(naive_dt, is_dst=None)
                    utc_dt = local_dt.astimezone(pytz.utc)
                    utc_dts.append(utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
                start_time = utc_dts[0]
                end_time = utc_dts[1]
            else:
                error_message = 'Time Zone is None for Event %s ' % event_name
                log_error(
                    dict(
                        error=error_message,
                        functionName='gt_to_sn_fields_mapping',
                        fileName=__file__,
                        user=self.user.name
                    )
                )
            currency = data['currency']
            time_zone = data['timezone']

            # Creating ticket data as Eventbrite wants us to associate tickets
            # with events
            venue_name = 'Event Address'
            number_of_tickets = data['max_attendees']
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

            venue = Venue.get_by_id(data['venue_id'])
            # This dict is used to create venue for a specified event
            self.venue_payload = {
                'venue.name': venue_name,
                'venue.address.address_1': venue.address_line1,
                'venue.address.address_2': venue.address_line2,
                'venue.address.region': venue.state,
                'venue.address.city': venue.city,
                # 'venue.address.country': venue.country,
                'venue.address.postal_code': venue.zipcode,
                'venue.address.latitude': venue.latitude,
                'venue.address.longitude': venue.longitude,
            }
            # This dict is used to create tickets for a specified event
            self.ticket_payload = {
                'ticket_class.name': ticket_type,
                'ticket_class.quantity_total': number_of_tickets,
                'ticket_class.free': free_tickets,
            }
            self.social_network_event_id = data.get('social_network_event_id')
        else:
            log_error(
                dict(
                    error='Data is None',
                    functionName='gt_to_sn_fields_mapping',
                    fileName=__file__,
                    user=self.user.name
                )
            )

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
        if (user_credentials.user_id == user_credentials.user_id) \
                and (user_credentials.social_network_id == user_credentials.social_network_id) \
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
                    log_exception(
                        dict(
                            error=e.message,
                            functionName='create_webhook',
                            fileName=__file__,
                            user=self.user.name
                        )
                    )
            else:
                log_error(
                    dict(
                        error="Eventbrite Webhook wasn't created successfully",
                        functionName='create_webhook',
                        fileName=__file__,
                        user=self.user.name
                    )
                )
        else:
            # webhook has already been created for this user
            status = True
        return status