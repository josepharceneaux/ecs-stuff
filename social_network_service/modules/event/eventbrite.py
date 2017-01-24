"""
This modules contains Eventbrite class. It inherits from EventBase class.
Eventbrite contains methods to create, update, get, delete events.
It also contains methods to get RSVPs of events.
"""

# Standard Library
from datetime import datetime
from datetime import timedelta

# Application specific
from social_network_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls as Urls
from social_network_service.modules.urls import get_url
from social_network_service.modules.utilities import logger
from social_network_service.modules.utilities import log_error
from social_network_service.common.models.venue import Venue
from social_network_service.common.models.event import Event
from social_network_service.modules.event.base import EventBase
from social_network_service.custom_exceptions import EventNotCreated
from social_network_service.custom_exceptions import TicketsNotCreated
from social_network_service.custom_exceptions import EventNotPublished
from social_network_service.custom_exceptions import EventInputMissing
from social_network_service.custom_exceptions import EventLocationNotCreated
from social_network_service.common.utils.datetime_utils import DatetimeUtils
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.custom_exceptions import VenueNotFound
from social_network_service.social_network_app import app


class Eventbrite(EventBase):
    """
    This class inherits from EventBase class.
    This implements the abstract methods defined in EventBase class.
    It also implements methods to create, update , retrieve and delete (unpublish)
     event on Eventbrite website.

    :Example:

        To create / update a Eventbrite event you have to do tha following:

        1. Create Eventbrite instance
            eventbrite = Eventbrite(user=user_obj,
                            headers=authentication_headers
                            )
        2. Then first create Eventbrite specific event data by calling
            event_gt_to_sn_mapping()
            eventbrite.event_gt_to_sn_mapping(data)

            it will add parsed data to 'self.payload' dictionary

        3. Now call create_event() / update_event()  which will
                get venue from db given by venue_id (local db venue id) in
                self.payload.
                if venue in db contains 'social_network_venue_id', it means
                that venues has already been created on Eventbrite so no need
                to create again on Eventbrite, just return that id to be passed
                in self.payload.
                And if 'social_network_venue_id' in none, creates venue on
                Eventbrite and returns Eventbrite venue id. It now sends a POST
                request to Eventbrite API to create event and returns event

    """

    def __init__(self, *args, **kwargs):
        """
        This method initializes eventbrite object and assigns default/initial
        values.
        This object has following attributes:
            - events:
                a list of events from social network
            - rsvp:
                a list of RSVPs for events in 'events' list
            - data:
                a dictionary containing post request data to create event
            - user:
                User object  user who sent the request to create this object
            - user_credentials:
                user credentials for eventbrite for this user
            - social_network:
                SocialNetwork object representing Eventbrite SN
            - api_url:
                URL to access eventbrite API
            - member_id:
                user member id on eventbrite
            - venue_id:
                Id of the location for this event
            - event_payload:
                a dictionary containing data for event creation on eventbrite
            - tickets_payload:
                dictionary containing data for event tickets
            - venue_payload:
                dictionary containing data for location/ venue to be added on
                eventbrite
            - social_network_event_id:
                event id of event on eventbrite
            - start_date_in_utc:
                utc start_date for event importer
            - end_date_in_utc:
                utc start_date for event importer

        :param kwargs: datetime range dict or None
        """
        super(Eventbrite, self).__init__(*args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.event_payload = None
        self.social_network_event_id = None
        self.ticket_payload = None
        self.venue_payload = None
        self.start_date_in_utc =\
            kwargs.get('date_range_start') \
            or (datetime.utcnow() -
                timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.end_date_in_utc =\
            kwargs.get('date_range_end') \
            or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.cancelled_status = ('deleted', 'canceled', 'ended')

    def get_events(self, status='live', order_by='start_asc'):
        """
        We send GET requests to Eventbrite API and get already created events
        by this user on eventbrite.com.
        We also have to handle pagination because Eventbrite's API does that
        too.
        :return all_events: a collection of eventbrite events for specific user
        :rtype all_events: list
        """
        # create url to fetch events from eventbrite.com
        search = str(self.member_id) + '/owned_events'
        events_url = get_url(self, Urls.USER).format(search)
        params = {
            'status': status
        }
        # initialize event list to empty
        all_events = []
        try:
            # send a GET request to eventbrite's api to get events for given
            # user and after start_date
            response = http_request('GET', events_url,
                                    params=params,
                                    headers=self.headers,
                                    user_id=self.user.id)
        except:
            logger.exception('get_events: user_id: %s' % self.user.id)
            raise

        if response.ok:
            # if response is ok, get json data
            data = response.json()
            all_events.extend(data['events'])
            current_page = 1
            total_pages = data['pagination']['page_count']
            for page in range(1, total_pages):
                params_copy = params.copy()
                current_page += 1
                params_copy['page'] = current_page
                try:
                    # get data for every page
                    response = http_request('GET', events_url,
                                            params=params_copy,
                                            headers=self.headers,
                                            user_id=self.user.id)
                except Exception as e:
                    logger.exception('get_events: user_id: %s' % self.user.id)

                if response.ok:
                    data = response.json()
                all_events.extend(data['events'])
        return all_events

    def event_sn_to_gt_mapping(self, event):
        """
        We take event's data from social network's API and map its fields to
        getTalent database fields. Finally we return Event's object to
        save/update record in getTalent database.
        We also issue some calls to get updated venue and organizer information.
        :param event: data from eventbrite API.
        :type event: dictionary
        :exception Exception: It raises exception if there is an error getting
            data from API.
        :return: event_data, venue_data: event dict object,  venue dict data
        :rtype tuple: event and venue dict data
        """
        venue_obj = None
        venue_data = None
        assert event is not None
        # Get information about event's venue
        venue_id = event.get('venue_id')
        if venue_id:
            venue_obj = Venue.get_by_user_id_and_social_network_venue_id(self.user.id, venue_id)
            if not venue_obj:
                try:
                    # Get venues from Eventbrite API for this event.
                    response = http_request('GET',
                                            get_url(self, Urls.VENUE).format(event['venue_id']),
                                            headers=self.headers,
                                            user_id=self.user.id)
                except:
                    logger.exception('event_sn_to_gt_mapping: user_id: %s,'
                                     'social_network_event_id: %s' % (self.user.id, event['id']))
                    raise
                if response.ok:
                    # get json data for venue
                    venue = response.json()
                    venue_data = dict(
                        social_network_id=self.social_network.id,
                        social_network_venue_id=event['venue_id'],
                        user_id=self.user.id,
                        address_line_1=venue['address']['address_1'],
                        address_line_2=venue['address']['address_2'],
                        city=venue['address']['city'],
                        state=venue['address']['region'],
                        zip_code=venue['address']['postal_code'],
                        country=venue['address']['country'],
                        longitude=float(venue['address']['longitude']) if venue and venue.has_key('address') else 0,
                        latitude=float(venue['address']['latitude']) if venue and venue.has_key('address') else 0
                    )

        # return Event object
        event_data = dict(
            social_network_event_id=event['id'],
            title=event['name']['text'],
            description=event['description']['html'],
            social_network_id=self.social_network.id,
            user_id=self.user.id,
            social_network_group_id=0,
            url=event.get('url'),
            group_url_name='',
            venue_id=venue_obj.id if venue_obj else None,
            start_datetime=event['start']['local'],
            end_datetime=event['end']['local'],
            registration_instruction='',
            cost=0,
            currency=event['currency'],
            timezone=event['start']['timezone'],
            max_attendees=event['capacity']
        )
        return event_data, venue_data

    def create_event(self):
        """
        This function is used to post/create event on Eventbrite.com
        It uses create_tickets() method to allow user subscriptions and
        publish_event() to make it public
        :exception EventNotCreated: throws exception if unable to create
            event on Eventbrite.com
        :return: event_id, tickets_id: a tuple containing event_id on
            Eventbrite and tickets_id for this event

            :Example:

                In order to create event first create EventBrite object and it
                takes user and authentication headers e.g.

                >> eventbrite = Eventbrite(user=gt_user,
                                           headers=authentication_headers)

                Then call event_gt_to_sn_mapping() method on this object and
                 pass it event dictionary.
                >> eventbrite.event_gt_to_sn_mapping(event_data)

                It will create event payload which is required to post event on
                Eventbrite.com
                Now call create event to create event on Eventbrite.com

                >> eventbrite.create_event()

                This method returns id of getTalent event that was created on
                 Eventbrite.com as well.

        """
        # create url to post/create event on eventbrite.com
        url = get_url(self, Urls.EVENTS)
        # adding venue for the event or reuse if already created on
        # eventbrite.com
        venue_id = self.add_location()
        # add venue_id in event payload so it can be associated with this event
        # on eventbrite
        self.event_payload['event.venue_id'] = venue_id
        # create event on eventbrite by sending POST request
        response = http_request('POST', url, params=self.event_payload,
                                headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            # Event has been created on vendor and saved in draft there.
            # Now we need to create tickets for it and then publish it.
            event = response.json()
            event_id = event['id']
            # Ticket are going to be created/updated
            ticket_id = self.create_tickets(event_id)
            # Ticket(s) have been created for newly created Event
            if app.config[TalentConfigKeys.ENV_KEY] not in [TalentEnvs.JENKINS]:
                self.publish_event(event_id)
            logger.info('|  Event %s created Successfully  |' % self.event_payload['event.name.html'])
            self.data['social_network_event_id'] = event_id
            self.data['tickets_id'] = ticket_id
            self.data['url'] = event['url']
            return self.save_event()
        else:
            error_message = 'Event was not created Successfully as draft'
            response = response.json()
            error_detail = response.get('error', '') + ': ' \
                           + response.get('error_description', '')
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
        It uses update_tickets() method to update number of tickets for this
         event

        :exception EventNotCreated: throws exception if unable to update event
         on Eventbrite.com)
        :return: id of event
        :rtype: int

            :Example:

                In order to updates event first create EventBrite object and it
                takes user and authentication headers e.g.

                >> eventbrite = Eventbrite(user=gt_user,
                                           headers=authentication_headers)

                Then call event_gt_to_sn_mapping() method on this object and
                pass it event dictionary.
                >> eventbrite.event_gt_to_sn_mapping(event_data)

                It will create event payload which is required to post event on
                Eventbrite.com.
                Now call update_event to update event on Eventbrite.com and in
                getTalent database.

                >> eventbrite.update_event()

                This method returns id of updated getTalent event.
        """
        # create url to update event
        url = get_url(self, Urls.EVENT).format(str(self.social_network_event_id) + '/')
        venue_id = self.add_location()  # adding venue for the event
        self.event_payload['event.venue_id'] = venue_id
        response = http_request('POST', url, params=self.event_payload,
                                headers=self.headers,
                                user_id=self.user.id)
        if response.ok:  # event has been updated on Eventbrite.com
            event_id = response.json()['id']
            # Ticket are going to be created/updated
            ticket_id = self.update_tickets(event_id)
            logger.info('|  Event %s updated Successfully  |'
                        % self.event_payload['event.name.html'])
            self.data['social_network_event_id'] = event_id
            self.data['tickets_id'] = ticket_id
            return self.save_event()
        else:
            error_message = 'Event was not updated Successfully'
            response = response.json()
            error_detail = response.get('error', '') + ': ' \
                           + response.get('error_description', '')
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
        :exception EventLocationNotCreated: throws exception if unable to
            create or update venue on Eventbrite
        :exception VenueNotFound: raises exception if venue does not exist
            in database
        :return venue_id: id for venue created on eventbrite.com
        :rtype venue_id: int

            :Example:

                This method is used to create venue or location for event
                on Eventbrite. It requires a venue already created in getTalent
                database otherwise it will raise VenueNotFound exception.

                Given venue id it first gets venue from database and uses its
                data to create Eventbrite object

                >> eventbrite = Eventbrite(user=gt_user,
                                           headers=authentication_headers)

                Then we call add location from create event
                To get a better understanding see *create_event()* method.


        """
        # get venue from db which will be created on Eventbrite
        venue = Venue.get_by_user_id_social_network_id_venue_id(
            self.user.id, self.social_network.id, self.venue_id)
        if venue:
            if venue.social_network_venue_id:
                # there is already a venue on Eventbrite with this info.
                return venue.social_network_venue_id
            # This dict is used to create venue
            payload = {
                'venue.name': venue.address_line_1,
                'venue.address.address_1': venue.address_line_1,
                'venue.address.address_2': venue.address_line_2,
                'venue.address.region': venue.state,
                'venue.address.city': venue.city,
                # 'venue.address.country': venue.country,
                'venue.address.postal_code': venue.zip_code,
                'venue.address.latitude': venue.latitude,
                'venue.address.longitude': venue.longitude,
            }
            # create url to send post request to create venue
            url = get_url(self, Urls.VENUES)
            response = http_request('POST', url, params=payload,
                                    headers=self.headers,
                                    user_id=self.user.id)
            if response.ok:
                logger.info('|  Venue has been created  |')
                venue_id = response.json().get('id')
                venue.update(social_network_venue_id=venue_id)
                return venue_id
            else:
                error_message = "Venue was not Created. There are some " \
                                "errors: Details: %s " % response
                message = '\nErrors from the Social Network:\n'
                message += \
                    ''.join(response.json().get('error') + ','
                            + response.json().get('error_description'))
                error_message += message
                log_error({'error': error_message,
                           'user_id': self.user.id
                           })
                raise EventLocationNotCreated(
                    'ApiError: Unable to create venue for event\n %s'
                    % message)
        else:
            error_message = 'Venue with ID = %s does not exist in db.' \
                            % self.venue_id
            log_error({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise VenueNotFound('Venue not found in database. Kindly create'
                                ' venue first.')

    def create_tickets(self, social_network_event_id):
        """
        This method creates tickets for specific event on Eventbrite.com.
        This method should be called after creating event on social_network.
        See "social_network_service.event.Eventbrite.create_event" method for
        further info
        :param social_network_event_id: event id which refers to event on
            eventbrite.com
        :type social_network_event_id: str
        :exception TicketsNotCreated (throws exception if unable to
            create tickets)
        :return: tickets_id (an id which refers to tickets created on
            eventbrite.com
        :rtype: str
        """
        tickets_url = get_url(self, Urls.TICKETS).format(social_network_event_id)
        return self.manage_event_tickets(tickets_url)

    def update_tickets(self, social_network_event_id):
        """
        This method update tickets for specific event on Eventbrite.com.
        This method should be called after updating event contents on
        social_network.
        See "social_network_service.event.Eventbrite.update_event" method for
            further info
        :param social_network_event_id: event id which refers to event on
        eventbrite.com
        :type social_network_event_id: str
        :exception TicketsNotCreated (throws exception if unable to update
            tickets)
        :return: tickets_id (an id which refers to tickets updated on
            eventbrite.com)
        :rtype: str
        """
        tickets_url = get_url(self, Urls.TICKETS).format(social_network_event_id)
        event = Event.get_by_user_and_social_network_event_id(
            self.user.id, social_network_event_id)
        if event.tickets_id:
            tickets_url = tickets_url + str(event.tickets_id) + '/'
        else:
            logger.info('Tickets ID is not available for event with id %s,'
                        ' User:  %s' % (social_network_event_id,
                                        self.user.name))
            raise TicketsNotCreated('ApiError: Unable to update event tickets'
                                    ' on Eventbrite as tickets_id was not '
                                    'found for this event')
        return self.manage_event_tickets(tickets_url)

    def manage_event_tickets(self, tickets_url):
        """
        Here tickets are created for event on Eventbrite.
        This method sends a POST request to Eventbrite.com API to create or
        update tickets. Call this method from create_tickets or update_tickets
        with respective tickets_url. It returns tickets id if successful
        otherwise raises "TicketsNotCreated" exception

        :param tickets_url  (API url to create or update event tickets)
        :type tickets_url: str
        :exception TicketsNotCreated (throws exception if unable to create or
            update tickets)
        :return: tickets_id (an id which refers to tickets for event on
            eventbrite.com)
        :rtype: str
        """
        # send POST request to create or update tickets for event
        response = http_request('POST', tickets_url, params=self.ticket_payload,
                                headers=self.headers, user_id=self.user.id)
        if response.ok:
            logger.info('|  %s Ticket(s) have been created  |'
                        % str(self.ticket_payload['ticket_class.quantity_total']
            ))
            tickets_id = response.json().get('id')
            return tickets_id
        else:
            error_message = 'Event tickets were not created successfully'
            log_error({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise TicketsNotCreated('ApiError: Unable to create event tickets '
                                    'on Eventbrite')

    def publish_event(self, social_network_event_id):
        """
        This function publishes the Event on Eventbrite.
        This event is public.
        :param social_network_event_id: id for event on eventbrite.com
        :type social_network_event_id: int
        :exception EventNotPublished: raises this exception when unable to
            publish event on Eventbrite.com
        """
        # create url to publish event
        url = get_url(self, Urls.PUBLISH_EVENT).format(str(social_network_event_id))
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers, user_id=self.user.id)
        if response.ok:
            logger.info('|  Event has been published  |')
        else:
            error_message = "Event was not Published. There are some " \
                            "errors: Details: %s  |" % response.text
            log_error({
                'user_id': self.user.id,
                'error': error_message,
            })
            raise EventNotPublished('ApiError: Unable to publish event '
                                    'on Eventbrite')

    @staticmethod
    def validate_required_fields(data):
        """
        Here we validate that all the required fields for the event creation on
        Eventbrite are filled. If any required filed is missing, raises
        exception named EventInputMissing.
        :param data: dictionary containing event data
        :type data: dict
        :exception EventInputMissing: raises exception if all required fields
            are not found
        """
        mandatory_input_data = ['title', 'description', 'end_datetime', 'max_attendees',
                                'timezone', 'start_datetime', 'currency', 'venue_id']
        # gets fields which are missing
        missing_items = [key for key in mandatory_input_data
                         if not data.get(key)]
        if missing_items:
            raise EventInputMissing("Mandatory Input Missing: %s"
                                    % missing_items)
        EventBase.validate_required_fields(data)

    def event_gt_to_sn_mapping(self, data):
        """
        This is actually the mapping of data from the input data from
        EventCreationForm to the data required for API calls on Eventbrite.
        :param data: dictionary containing event data
        :type data: dict
        :exception KeyError: can raise KeyError if some key not found in
            event data

            : Example:

                This method takes getTalent specific event data in following
                 format.

                data = {
                        "organizer_id": 1,
                        "venue_id": 1,
                        "title": "Test Event",
                        "description": "Test Event Description",
                        "registration_instruction": "Just Come",
                        "end_datetime": "30 Oct, 2015 04:51 pm",
                        "group_url_name": "QC-Python-Learning",
                        "social_network_id": 13,
                        "timezone": "Asia/Karachi",
                        "cost": 0,
                        "start_datetime": "25 Oct, 2015 04:50 pm",
                        "currency": "USD",
                        "social_network_group_id": 18837246,
                        "max_attendees": 10
                }

                And then makes Eventbrite specific data like this

                event_payload = {
                                    'event.start.utc': '2015-10-30T11:51:00Z',
                                    'event.start.timezone': "Asia/Karachi",
                                    'event.end.utc': '2015-10-25T11:50:00Z',
                                    'event.end.timezone': "Asia/Karachi",
                                    'event.currency': 'USD',
                                    'event.name.html': 'Test Event',
                                    'event.description.html':
                                                    'Test Event Description'
                                }
                ticket_payload = {
                                    'ticket_class.name': 'Event Ticket',
                                    'ticket_class.quantity_total': 10,
                                    'ticket_class.free': True,
                                }
        """
        assert data, 'Data should not be None/empty'
        assert isinstance(data, dict), 'Data should be a dictionary'
        self.data = data
        self.validate_required_fields(data)
        # convert datetime strings to datetime objects
        super(Eventbrite, self).event_gt_to_sn_mapping(data)
        # Eventbrite assumes that provided start and end DateTime is in UTC
        # So, form given Timezone, (eventTimeZone in our case), it changes the
        # provided DateTime accordingly.
        start_time = DatetimeUtils.get_utc_datetime(data['start_datetime'], data['timezone'])
        end_time = DatetimeUtils.get_utc_datetime(data['end_datetime'], data['timezone'])

        # This dict is used to create an event as a draft on vendor
        self.event_payload = {
            'event.start.utc': start_time,
            'event.start.timezone': data['timezone'],
            'event.end.utc': end_time,
            'event.end.timezone': data['timezone'],
            'event.currency': data['currency'],
            'event.name.html': data['title'],
            'event.description.html': data['description']
        }
        self.venue_id = data['venue_id']
        # Creating ticket data as Eventbrite wants us to associate tickets with
        # events. This dict is used to create tickets for a specified event.

        max_attendees = data['max_attendees']
        cost = data.get('cost')
        if max_attendees and cost:
            self.ticket_payload = {
                'ticket_class.name': 'Event Ticket',
                'ticket_class.quantity_total': max_attendees,
                'ticket_class.cost': 'USD,' + str(cost) + '00'
            }
        else:
            self.ticket_payload = {
                'ticket_class.name': 'Event Ticket',
                'ticket_class.quantity_total': max_attendees,
                'ticket_class.free': True,
            }
        self.social_network_event_id = data.get('social_network_event_id')
