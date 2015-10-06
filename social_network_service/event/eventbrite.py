"""
This modules contains Eventbrite class. It inherits from EventBase class.
Eventbrite contains methods to create, update, get, delete events.
It alos contains methods to get events RSVPs.
"""
import pytz
import json

from datetime import datetime
from datetime import timedelta
from social_network_service.custom_exections import EventNotCreated, \
    VenueNotFound, TicketsNotCreated, EventNotPublished, EventInputMissing, \
    EventLocationNotCreated
from common.models.organizer import Organizer
from common.models.venue import Venue
from social_network_service.event.base import EventBase
from social_network_service.utilities import log_error, logger, log_exception, \
    http_request
from common.models.event import Event
from flask import current_app as app
EVENTBRITE = 'Eventbrite'
WEBHOOK_REDIRECT_URL = app.config['WEBHOOK_REDIRECT_URL']


class Eventbrite(EventBase):
    """
    This class inherits from EventBase class.
    This implements the abstract methods defined in interface.
    It also implements functions to create event on Eventbrite website.
    """

    def __init__(self, *args, **kwargs):
        """
        This method initializes eventbrite object and assigns default/initial values.
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
        We send GET requests to Eventbrite API and get already created events by this useron eventbrite.com.
        We also have to handle pagination because Eventbrite's API does that too.
        :return all_events: a collection of eventbrite events for specific user
        :rtype all_events: list
        """
        # create url to fetch events from eventbrite.com
        events_url = self.api_url + '/events/search/'
        params = {'user.id': self.member_id,
                  'date_created.range_start': self.start_date_in_utc
                  }
        # initialize event list to empty
        all_events = []
        try:
            # send a GET request to eventbrite.com api to get events for given user and after start_date
            response = http_request('GET', events_url,
                                    params=params,
                                    headers=self.headers,
                                    user_id=self.user.id)
        except Exception as error:
            log_exception({'user_id': self.user.id,
                           'error': error.message})
            raise
        if response.ok:
            # if response is ok, get json data
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
                    # get data for every page
                    response = http_request('GET', events_url, params=params_copy,
                                            headers=self.headers, user_id=self.user.id)
                except Exception as error:
                    log_exception({'user_id': self.user.id,
                                   'error': error.message})
                    raise
                if response.ok:
                    data = response.json()
                all_events.extend(data['events'])
            return all_events
        return all_events

    def event_sn_to_gt_mapping(self, event):
        """
        Basically we take event's data from Eventbrite's end
        and map their fields to getTalent database specific data and finally we return
        Event's object. We also issue some calls to get updated
        venue and organizer information.
        :param event: data from eventbrite API.
        :type event: dictionary
        :exception Exception: It raises exception if there is an error getting data from API.
        :return: event: Event object
        :rtype event: common.models.event.Event
        """
        organizer = None
        organizer_email = None
        venue = None
        organizer_id = None
        venue_id = None
        assert event is not None
        # Get information about event's venue
        if event['venue_id']:
            try:
                # Get venues from Eventbrite API for this event.
                response = http_request('GET', self.api_url + '/venues/' + event['venue_id'],
                                        headers=self.headers,
                                        user_id=self.user.id)
            except Exception as error:
                log_exception({'user_id': self.user.id,
                               'error': error.message})
                raise
            if response.ok:
                # get json data for venue
                venue = response.json()
                # Now let's try to get the information about the event's organizer
                if event['organizer_id']:
                    try:
                        # Get organizer of the event from Eventbrite API.
                        response = http_request('GET', self.api_url +
                                                '/organizers/' + event['organizer_id'],
                                                headers=self.headers,
                                                user_id=self.user.id)
                    except Exception as error:
                        log_exception({'user_id': self.user.id,
                                       'error': error.message})
                        raise
                    if response.ok:
                        # Get json data  for organizer
                        organizer = json.loads(response.text)
                    if organizer:
                        try:
                            response = http_request('GET', self.api_url + '/users/'
                                                    + self.member_id,
                                                    headers=self.headers,
                                                    user_id=self.user.id)
                        except Exception as error:
                            log_exception({'user_id': self.user.id,
                                           'error': error.message})
                            raise
                        if response.ok:
                            organizer_info = json.loads(response.text)
                            organizer_email = organizer_info['emails'][0]['email']

        if organizer:
            organizer_data = dict(
                user_id=self.user.id,
                name=organizer['name'] if organizer.has_key('name') else '',
                email=organizer_email if organizer_email else '',
                about=organizer['description'] if organizer.has_key('description') else ''

            )
            organizer_in_db = Organizer.get_by_user_id_and_name(
                self.user.id,
                organizer['name'] if organizer.has_key('name') else ''
                                                              )
            if organizer_in_db:
                organizer_in_db.update(**organizer_data)
                organizer_id = organizer_in_db.id
            else:
                organizer_instance = Organizer(**organizer_data)
                Organizer.save(organizer_instance)
                organizer_id = organizer_instance.id
        if venue:
            venue_data = dict(
                social_network_venue_id=event['venue_id'],
                user_id=self.user.id,
                address_line1=venue['address']['address_1'] if venue else '',
                address_line2=venue['address']['address_2'] if venue else '',
                city=venue['address']['city'] if venue else '',
                state=venue['address']['region'] if venue else '',
                zipcode=None,
                country=venue['address']['country'] if venue else '',
                longitude=float(venue['address']['longitude']) if venue else 0,
                latitude=float(venue['address']['latitude']) if venue else 0,
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
        # return Event object
        return Event(
            social_network_event_id=event['id'],
            title=event['name']['text'],
            description=event['description']['text'],
            social_network_id=self.social_network.id,
            user_id=self.user.id,
            group_id=0,
            url='',
            group_url_name='',
            organizer_id=organizer_id,
            venue_id=venue_id,
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
        This function is used to post/create event on Eventbrite.com
        It uses create_tickets() method to allow user subscriptions and publish_event() to make it public

        :exception EventNotCreated: throws exception if unable to create event on Eventbrite.com
        :return: event_id, tickets_id: a tuple containing event_id on Eventbrite and tickets_id for this event
        """
        # create url to post/create event on eventbrite.com
        url = self.api_url + "/events/"
        # adding venue for the event or reuse if already created on eventbrite.com
        venue_id = self.add_location()
        # add venue_id in event payload so it can be associated with this event on eventbrite
        self.event_payload['event.venue_id'] = venue_id
        # create event on eventbrite by sending POST request
        response = http_request('POST', url, params=self.event_payload, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            # event has been created on vendor and saved in draft there
            # Now we need to create tickets for it and then publish it.
            event_id = response.json()['id']
            # Ticket are going to be created/updated
            ticket_id = self.create_tickets(event_id)
            # Ticket(s) have been created for new created Event
            self.publish_event(event_id)
            logger.info('|  Event %s created Successfully  |'
                        % self.event_payload['event.name.html'])
            return event_id, ticket_id
        else:
            error_message = 'Event was not created Successfully as draft'
            response = response.json()
            error_detail = response.get('error', '') + ': ' + response.get('error_description', '')
            if error_detail != ': ':
                error_message += '\n%s' % error_detail
            log_error({
                'user_id': self.user.id,
                'error': error_detail,
            })
            raise EventNotCreated(error_message)

    def update_event(self):
        """
        This function is used to update an event on Eventbrite.com
        It uses update_tickets() method to update number of tickets for this event

        :exception EventNotCreated: throws exception if unable to update event on Eventbrite.com)
        :return: event_id, tickets_id: a tuple containing event_id on Eventbrite and tickets_id for this event)
        """
        # create url to update event
        url = self.api_url + "/events/" + str(self.social_network_event_id) + '/'
        venue_id = self.add_location()  # adding venue for the event
        self.event_payload['event.venue_id'] = venue_id
        response = http_request('POST', url, params=self.event_payload, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:  # event has been updated on Eventbrite.com
            event_id = response.json()['id']
            # Ticket are going to be created/updated
            ticket_id = self.update_tickets(event_id)
            logger.info('|  Event %s updated Successfully  |'
                        % self.event_payload['event.name.html'])
            return event_id, ticket_id
        else:
            error_message = 'Event was not updated Successfully'
            response = response.json()
            error_detail = response.get('error', '') + ': ' + response.get('error_description', '')
            if error_detail != ': ':
                error_message += '\n%s' % error_detail
            log_error({
                'user_id': self.user.id,
                'error': error_detail,
            })
            raise EventNotCreated(error_message)

    def add_location(self):
        """
        This generates a venue object for the event and returns the
        id of venue.
        :exception EventLocationNotCreated: throws exception if unable to create or update venue on Eventbrite
        :exception VenueNotFound: raises exception if venue does not exist in database
        :return venue_id: id for venue created on eventbrite.com
        :rtype venue_id: int
        """
        # get venue from db which will be created on Eventbrite
        venue = Venue.get_by_user_id_social_network_id_venue_id(self.user.id,
                                                                self.social_network.id,
                                                                self.venue_id)
        if venue:
            if venue.social_network_venue_id:
                # there is already a venue on Eventbrite with this info.
                return venue.social_network_venue_id
            # This dict is used to create venue
            payload = {
                'venue.name': venue.address_line1,
                'venue.address.address_1': venue.address_line1,
                'venue.address.address_2': venue.address_line2,
                'venue.address.region': venue.state,
                'venue.address.city': venue.city,
                # 'venue.address.country': venue.country,
                'venue.address.postal_code': venue.zipcode,
                'venue.address.latitude': venue.latitude,
                'venue.address.longitude': venue.longitude,
            }
            # create url to send post request to create venue
            url = self.api_url + "/venues/"
            response = http_request('POST', url, params=payload, headers=self.headers,
                                    user_id=self.user.id)
            if response.ok:
                logger.info('|  Venue has been created  |')
                venue_id = response.json().get('id')
                venue.update(social_network_venue_id=venue_id)
                return venue_id
            else:
                error_message = "Venue was not Created. There are some errors: " \
                                "Details: %s " % response
                message = '\nErrors from the Social Network:\n'
                message += ''.join(response.json().get('error') + ',' + response.json().get('error_description'))
                error_message += message
                log_error({'error': error_message,
                           'user_id': self.user.id
                           })
                raise EventLocationNotCreated('ApiError: Unable to create venue for event\n %s' % message)
        else:
            error_message = 'Venue with ID = %s does not exist in db.' % self.venue_id
            log_error({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise VenueNotFound('Venue not found in database. Kindly create venue first.')

    def create_tickets(self, event_id):
        """
        This method creates tickets for specific event on Eventbrite.com.
        This method should be called after creating event on social_network.
        See "social_network_service.event.Eventbrite.create_event" method for further info
        :param event_id: event id which refers to event on eventbrite.com
        :exception TicketsNotCreated (throws exception if unable to create tickets)
        :return: tickets_id (an id which refers to tickets created on eventbrite.com
        """
        tickets_url = self.api_url + "/events/" + event_id + "/ticket_classes/"
        return self.manage_event_tickets(tickets_url)

    def update_tickets(self, event_id):
        """
        This method updated tickets for specific event on Eventbrite.com.
        This method should be called after updating event contents on social_network.
        See "social_network_service.event.Eventbrite.update_event" method for further info
        :param event_id: event id which refers to event on eventbrite.com
        :exception TicketsNotCreated (throws exception if unable to update tickets)
        :return: tickets_id (an id which refers to tickets updated on eventbrite.com
        """
        tickets_url = self.api_url + "/events/" + event_id + "/ticket_classes/"
        event = Event.get_by_user_and_social_network_event_id(self.user.id, event_id)
        if event.tickets_id:
            tickets_url = tickets_url + str(event.tickets_id) + '/'
        else:
            logger.info('Tickets ID is not available for event with id %s, User:  %s'
                        % (event_id, self.user.name))
            raise TicketsNotCreated('ApiError: Unable to update event tickets on Eventbrite '
                                    'as tickets_id was not found for this event')
        return self.manage_event_tickets(tickets_url)

    def manage_event_tickets(self, tickets_url):
        """
        Here tickets are created for event on Eventbrite.
        This method sends a POST request to Eventbrite.com API to create or update tickets.
        Call this method from create_tickets or update_tickets with respective tickets_url.
        It returns tickets id if successful otherwise raises "TicketsNotCreated" ecxception

        :param tickets_url  (API url to create or update event tickets)
        :exception TicketsNotCreated (throws exception if unable to create or update tickets)
        :return: tickets_id (an id which refers to tickets for event on eventbrite.com
        """
        response = http_request('POST', tickets_url, params=self.ticket_payload,
                                headers=self.headers, user_id=self.user.id)
        if response.ok:
            logger.info('|  %s Ticket(s) have been created  |'
                        % str(self.ticket_payload['ticket_class.quantity_total']))
            tickets_id = response.json().get('id')
            return tickets_id
        else:
            error_message = 'Event tickets were not created successfully'
            log_error({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise TicketsNotCreated('ApiError: Unable to create event tickets on Eventbrite')

    def publish_event(self, event_id):
        """
        This function publishes the Event on Eventbrite.
        This event is public.
        :param event_id: id for event on eventbrite.com
        :type event_id: int
        :exception EventNotPublished: raises this exception when unable to publish event on Evntbrite.com
        :return:
        """
        # create url to publish event
        url = self.api_url + "/events/" + str(event_id) + "/publish/"
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers, user_id=self.user.id)
        if response.ok:
            logger.info('|  Event has been published  |')
        else:
            error_message = "Event was not Published. There are some errors: " \
                            "Details: %s  |" % response
            log_error({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise EventNotPublished('ApiError: Unable to publish event on specified social network')

    def unpublish_event(self, event_id, method='POST'):
        """
        This function is used when run unit test. It sets the api_relative_url
        and calls base class method to delete the Event from meetup which was
        created in the unit testing.
        :param event_id:id of newly created event
        :return: True if event is deleted from vendor, False other wsie
        """
        self.url_to_delete_event = self.api_url + "/events/" + str(event_id) + "/unpublish/"
        super(Eventbrite, self).unpublish_event(event_id, method=method)

    @staticmethod
    def validate_required_fields(data):
        """
        Here we validate that all the required fields for the event creation on
        Eventbrite are filled. If any required filed is missing, raises exception
        named  EventInputMissing.
        :param data: dictionary containing event data
        :type data: dict
        :exception EventInputMissing: raises exception if all required fields are not found
        """
        mandatory_input_data = ['title', 'description', 'end_datetime',
                                'timezone', 'start_datetime', 'currency']
        if not all([input in data and data[input] for input in mandatory_input_data]):
            log_error({
                'user_id': '',
                'error': 'Mandatory parameters missing in Eventbrite data'
            })
            raise EventInputMissing("Mandatory parameter missing in Eventbrite data.")

    def event_gt_to_sn_mapping(self, data):
        """
        This is actually the mapping of data from the input data from
        EventCreationForm to the data required for API calls on Eventbrite.
        :param data: dictionary containing event data
        :type data: dict
        :exception KeyError: can raise KeyError if some key not found in event data
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
                log_error({
                    'user_id': self.user.id,
                    'error': error_message
                })
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
            self.venue_id = data['venue_id']
            # This dict is used to create tickets for a specified event
            self.ticket_payload = {
                'ticket_class.name': ticket_type,
                'ticket_class.quantity_total': number_of_tickets,
                'ticket_class.free': free_tickets,
            }
            self.social_network_event_id = data.get('social_network_event_id')
        else:
            error_message = 'Data is None'
            log_error({
                'user_id': self.user.id,
                'error': error_message
            })

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
        status = False
        if (user_credentials.user_id == user_credentials.user_id) \
                and (user_credentials.social_network_id == user_credentials.social_network_id) \
                and (user_credentials.webhook in [None, '']):
            url = self.api_url + "/webhooks/"
            payload = {'endpoint_url': WEBHOOK_REDIRECT_URL}
            response = http_request('POST', url, params=payload, headers=self.headers,
                                    user_id=self.user.id)
            if response.ok:
                try:
                    webhook_id = response.json()['id']
                    user_credentials.update_record(webhook=webhook_id)
                    status = True
                except Exception as error:
                    log_exception({
                        'user_id': self.user.id,
                        'error': error.message
                    })
            else:
                error_message = "Eventbrite Webhook wasn't created successfully"
                log_exception({
                    'user_id': self.user.id,
                    'error': error_message
                })
        else:
            # webhook has already been created for this user
            status = True
        return status
