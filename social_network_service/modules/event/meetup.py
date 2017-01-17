"""
This modules contains Meetup class. It inherits from EventBase class.
Meetup contains methods to create, update, get, delete events.
It also contains methods to get RSVPs of events.
"""

# Standard Library
import json
from datetime import datetime
from datetime import timedelta
import time

# Application specific
from social_network_service.common.models.event import MeetupGroup
from social_network_service.common.models.venue import Venue
from social_network_service.modules.constants import MEETUP_VENUE
from social_network_service.modules.urls import get_url
from social_network_service.social_network_app import logger
from social_network_service.modules.utilities import log_error
from social_network_service.modules.event.base import EventBase
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.utilities import milliseconds_since_epoch_to_dt
from social_network_service.modules.utilities import milliseconds_since_epoch_local_time
from social_network_service.custom_exceptions import VenueNotFound
from social_network_service.custom_exceptions import EventNotCreated
from social_network_service.custom_exceptions import EventInputMissing
from social_network_service.custom_exceptions import EventLocationNotCreated
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls as Urls


class Meetup(EventBase):
    """
    This class is inherited from TalentEventBase class and
    it implements the abstract methods defined in interface.
    It also implements functions to create event on Meetup website

    :Example:

        To create / update a Meetup event you have to do tha following:

        1. Create Meetup instance
            meetup = Meetup(user=user_obj,
                            headers=authentication_headers
                            )
        2. Then first create Meetup specific event data by calling
            event_gt_to_sn_mapping()
            meetup.event_gt_to_sn_mapping(data)

            it will add parsed data to 'self.payload' dictionary

        3. Now call create_event() / update_event()  which will
                get venue from db given by venue_id (local db venue id) in
                self.payload.
                If venue in db contains 'social_network_venue_id', it means
                that venues has already been created on Meetup so no need to
                create again on Meetup, just return that id to be passed
                in self.payload.
                And if 'social_network_venue_id' is none, it creates venue on
                Meetup and returns Meetup venue id. It now sends a POST request
                to Meetup API to create event and returns event
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize required class variables to be used later.
        this object has following attributes:
            - events:
                a list of events from social network
            - rsvp:
                a list of RSVPs for events in 'events' list
            - data:
                a dictionary containing POST request data to create event
            - user:
                User object  user who sent the request to create this object
            - user_credentials:
                user credentials for Meetup for this user
            - social_network:
                SocialNetwork object representing Meetup SN
            - api_url:
                URL to access Meetup API
            - member_id:
                user member id on Meetup
            - venue_id:
                Id of the location for this event
            - payload:
                a dictionary containing data for event creation on Meetup
            - group_url_name:
                Meetup group name owned by this user
            - social_network_group_ids:
                list of group ids owned by user
            - social_network_event_id:
                event id of event on Meetup
            - start_time_since_epoch:
                time passed after epoch till start_time
            - end_time_since_epoch:
                time passed after epoch till end_time
        """
        super(Meetup, self).__init__(*args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.data = None
        self.payload = None
        self.group_url_name = None
        self.social_network_group_ids = []
        self.social_network_event_id = None
        # TODO: Change following start_date/end_date variable names to start_datetime/end_datetime
        self.start_date = kwargs.get('start_date') or (datetime.utcnow() - timedelta(days=5))
        self.end_date = kwargs.get('end_date') or (datetime.utcnow() + timedelta(days=5))
        self.start_time_since_epoch = milliseconds_since_epoch_local_time(self.start_date)
        self.end_time_since_epoch = milliseconds_since_epoch_local_time(self.end_date)

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Meetup's API
        does that too.
        :return: all_events: Events of getTalent user on Meetup.com
        :rtype all_events: list
        """
        all_events = []  # contains all events of gt-users
        # page size is 100 so if we have 500 records we will make
        # 5 requests (using pagination where each response will contain
        # 100 records).
        events_url = get_url(self, Urls.EVENTS)
        # we can specify status=upcoming,past,draft,cancelled etc. By default we
        # have status=upcoming, so we are not explicitly specifying in fields.
        meetup_groups = MeetupGroup.filter_by_keywords(user_id=self.user.id)
        if not meetup_groups:
            logger.warn('''No MeetupGroup is asscoiated with this user subscription for Meetup.
                           UserId: %s
                           MemberId: %s
                           ''' % (self.user.id, self.user_credentials.member_id))
            return all_events
        params = {
            'group_id': ','.join([str(group.group_id) for group in meetup_groups]),
            'status': "upcoming,proposed,suggested",
            'fields': 'timezone'
        }
        response = http_request('GET', events_url, params=params, headers=self.headers, user_id=self.user.id)
        if response.ok:
            data = response.json()
            all_events = []
            all_events.extend(data['results'])
            # next_url determines the pagination, this variable keeps
            # appearing in response if there are more pages and stops
            # showing up when there are no more.
            next_url = data['meta']['next'] or None
            while next_url:
                url = next_url
                # Sleep for 10 / 30 seconds to avoid throttling
                time.sleep(0.34)
                response = http_request('GET', url, headers=self.headers, user_id=self.user.id)
                if response.ok:
                    data = response.json()
                    all_events.extend(data['results'])
                    next_url = data['meta']['next'] or None
                    if not next_url:
                        break
        return all_events

    def _filter_event(self, event):
        """
        This method returns True if given event's group is owned by current user.
        :param event: event to be tested
        :type event: dict
        :return True or False
        :rtype Boolean
        """
        social_network_group_id = event['group'].get('id')
        # check if event's group id exists
        if social_network_group_id:
            if social_network_group_id in self.social_network_group_ids:
                return True
            url = get_url(self, Urls.GROUPS) + '/?sign=true'
            # Sleep for 10 / 30 seconds to avoid throttling
            time.sleep(0.34)
            response = http_request('GET', url,
                                    params={
                                        'group_id': social_network_group_id
                                    },
                                    headers=self.headers,
                                    user_id=self.user.id)
            if response.ok:
                group = response.json()
                group_organizer = group['results'][0]['organizer']
                # group_organizer contains a dict that has member_id and name
                if str(group_organizer['member_id']) == self.member_id:
                    # save this group id as user's owned groups, so no need to
                    # fetch it again
                    self.social_network_group_ids.append(social_network_group_id)
                    return True
        return False

    def event_sn_to_gt_mapping(self, event):
        """
        We take event's data from social network's API and map its fields to
        getTalent database fields. Finally we return Event's object to
        save/update record in getTalent database.
        We also issue some calls to get updated venue and organizer information.
        event object from Meetup API looks like

        {
            u'status': u'upcoming',
            u'utc_offset': -25200000,
            u'event_url': u'https://www.meetup.com/sfpython/events/234926670/',
            u'group': {
                        u'who': u'Python Programmers',
                        u'name': u'San Francisco Python Meetup Group',
                        u'group_lat': 37.77000045776367,
                        u'created': 1213377311000,
                        u'join_mode': u'open',
                        u'group_lon': -122.44000244140625,
                        u'urlname': u'sfpython',
                        u'id': 1187265
                    },
            u'description': u'<p>SF Python is bringing it\'s Project Night to TBA. Please come out and hack
                                with this great community we have built.</p> <p>We are really grateful that our
                                facility host TBA is sponsoring food and beverages (alcoholic and non-alcoholic)
                                for this event.</p> <p>Please email the leadership team if you are interested in:</p>
                            ',
              u'created': 1457407879000,
              u'updated': 1457407879000,
              u'visibility': u'public',
              "timezone": "US/Pacific",  // This field only appears when requested in `fields` parameters
              u'rsvp_limit': 75,  // This field only appears when we set RSVP settings while creating an event
              u'yes_rsvp_count': 2,
              u'waitlist_count': 0,
              u'maybe_rsvp_count': 0,
              u'time': 1505955600000,
              u'duration': 11700000,
              u'headcount': 0,
              u'id': u'gqjhrlywmbbc',
              u'name': u'Project Night at TBA'}

        :param event: data from Meetup's API
        :type event: dictionary
        :exception Exception: It raises exception if there is an error getting
            data from API.
        :return: event: Event object
        :rtype event: common.models.event.Event
        """
        venue_obj = None
        venue_data = None
        venue = event.get('venue')
        start_time = event.get('time')
        utc_offset = event.get('utc_offset')
        if start_time:
            start_time = milliseconds_since_epoch_to_dt(start_time + (utc_offset or 0))
        end_time = event.get('duration', None)
        if start_time and end_time:
            end_time = milliseconds_since_epoch_to_dt(event['time'] + end_time + (utc_offset or 0))

        if venue:
            # venue data looks like
            # {
            #       u'city': u'Cupertino', u'name': u'Meetup Address',
            #       u'country': u'US', u'lon': -122.030754,
            #       u'address_1': u'Infinite Loop', u'repinned': False,
            #       u'lat': 37.33167, u'id': 24062708
            # }
            venue_obj = Venue.get_by_user_id_and_social_network_venue_id(self.user.id, venue['id'])
            if not venue_obj:
                venue_data = dict(
                    social_network_id=self.social_network.id,
                    social_network_venue_id=venue['id'],
                    user_id=self.user.id,
                    address_line_1=venue.get('address_1', ''),
                    address_line_2=venue.get('name', ''),
                    city=venue.get('city', '').title().strip(),
                    state=venue.get('state', '').title().strip(),
                    zip_code=venue.get('zip'),
                    country=venue.get('country', '').title().strip(),
                    longitude=float(venue.get('lon', 0)),
                    latitude=float(venue.get('lat', 0))
                )

        event_data = dict(
            social_network_event_id=event['id'],
            title=event['name'],
            description=event.get('description', ''),
            social_network_id=self.social_network.id,
            user_id=self.user.id,
            venue_id=venue_obj.id if venue_obj else None,
            # group id and urlName are required fields to edit an event
            # so should raise exception if Null
            social_network_group_id=event['group']['id'],
            group_url_name=event['group']['urlname'],
            # Let's drop error logs if venue has no address, or if address
            # has no longitude/latitude
            url=event.get('event_url'),
            start_datetime=start_time,
            end_datetime=end_time,
            registration_instruction='',
            cost=0,
            currency='',
            timezone=event.get('timezone'),
            max_attendees=event.get('rsvp_limit')
        )
        return event_data, venue_data

    def add_location(self):
        """
        This function adds the location of event.
        :exception EventLocationNotCreated: raises exception if unable to
                  create venue on Meetup.com.
        :exception VenueNotFound: raises exception if unable to find venue
                  in getTalent database.
        :return id: id of venue created if creation is successful.
        :rtype id: int

            :Example:

                This method is used to create venue or location for event on
                Meetup.
                It requires a venue already created in getTalent database
                otherwise it will raise VenueNotFound exception.

                Given venue id it first gets venue from database and uses its
                data to create Meetup object

                >> meetup = Meetup(user=gt_user, headers=authentication_headers)

                Then we call add location from create event
                To get a better understanding see *create_event()* method.
        """
        venue_in_db = Venue.get_by_user_id_social_network_id_venue_id(
            self.user.id, self.social_network.id, self.venue_id)
        if not venue_in_db:
            error_message = 'Venue does not exist in db. Venue id is {}'.format(self.venue_id)
            log_error({'user_id': self.user.id, 'error': error_message})
            raise VenueNotFound('Venue not found in database. Kindly specify a valid venue.')

        if venue_in_db.social_network_venue_id:
            return venue_in_db.social_network_venue_id
        url = get_url(self, Urls.VENUES, custom_url=MEETUP_VENUE.format(self.group_url_name))
        logger.info('Creating venue for %s(user id:%s) using url:%s of API of %s.'
                    % (self.user.name, self.user.id, url, self.social_network.name))
        payload = {
            'address_1': venue_in_db.address_line_1,
            'address_2': venue_in_db.address_line_2,
            'city': venue_in_db.city,
            'country': venue_in_db.country,
            'state': venue_in_db.state,
            'name': venue_in_db.address_line_1
        }
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('POST', url, params=payload, headers=self.headers, user_id=self.user.id)
        if response.ok:
            venue_id = json.loads(response.text)['id']
            logger.info('|  Venue has been Added  |')
        elif response.status_code == 409:
            # 409 is returned when our venue is matching existing
            # venue/venues. So we pick the first one in potential
            # matches.
            try:
                venue_id = json.loads(response.text)[
                    'errors'][0]['potential_matches'][0]['id']
                logger.info('|  Venue was picked from matched records  |')
            except Exception as e:
                raise EventLocationNotCreated('ApiError: Unable to create venue for event',
                                              additional_error_info=dict(venue_error=str(e)))
        else:
            error_message = 'Venue was not Added. There are some errors.'
            errors = response.json().get('errors')
            message = '\nErrors from the social network:\n'
            message += '\n'.join(error['message'] + ', ' + error['code'] for error in errors) if errors else ''
            error_message += message
            log_error({'user_id': self.user.id, 'error': error_message})
            raise EventLocationNotCreated('ApiError: Unable to create venue for event\n %s' % message)
        venue_in_db.update(social_network_venue_id=venue_id)
        return venue_id

    def create_event(self):
        """
        This function is used to create Meetup event using vendor's API.
        It first creates a venue for event. Then venue_id is passed to
        event_payload.
        Then a POST request to Meetup API creates event on Meetup.com
        :exception EventNotCreated: raises exception if unable to
        publish/create event on Meetup.com.
        :return: id of event in db
        :rtype: int
        """
        venue_id = self.add_location()
        url = get_url(self, Urls.EVENT).format('')
        self.payload.update({'venue_id': venue_id, 'publish_status': 'published'})
        logger.info('Creating event for %s(user id:%s) using url:%s of API of %s.'
                    % (self.user.name, self.user.id, url, self.social_network.name))
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('POST', url, params=self.payload, headers=self.headers, user_id=self.user.id)
        if response.ok:
            event = response.json()
            event_id = event['id']
            logger.info('|  Event %s created Successfully  |' % self.payload['name'])
            self.data['social_network_event_id'] = event_id
            self.data['url'] = event.get('event_url', '')
            return self.save_event()
        else:
            error_message = 'Event was not Created. Error occurred during draft creation'
            log_error({'user_id': self.user.id, 'error': error_message})
            raise EventNotCreated('ApiError: Unable to create event on Meetup')

    def update_event(self):
        """
        It first creates/ updates a venue on Meetup.com and then passes that
        venue's id in event's payload to update event location along with event
        data.
        :exception EventNotCreated: raises exception if unable to update event
                on Meetup.com
        :return: id of event
        :rtype: int
        """
        # create url to update event
        url = get_url(self, Urls.EVENT).format(self.social_network_event_id)
        # create or update venue for event
        venue_id = self.add_location()
        # add venue id in event payload to update event venue on Meetup.com
        self.payload.update({'venue_id': venue_id})
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('POST', url, params=self.payload,
                                headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            event_id = response.json().get('id')
            logger.info('|  Event %s updated Successfully  |'
                        % self.payload['name'])
            self.data['social_network_event_id'] = event_id
            return self.save_event()
        else:
            error_message = 'Event was not created. Error occurred during ' \
                            'event update on Meetup'
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise EventNotCreated('ApiError: Unable to update event on Meetup')

    @staticmethod
    def validate_required_fields(data):
        """
        Here we validate that all the required fields for the event creation on
        Meetup are filled. If any required filed is missing, raises exception
        named  EventInputMissing.
        :param data: dictionary containing event data
        :type data: dict
        :exception EventInputMissing: raises exception if all required fields
         are not found in data dictionary.
        """
        # these are required fields for Meetup event
        mandatory_input_data = ['title', 'description', 'social_network_group_id',
                                'group_url_name', 'start_datetime', 'timezone',
                                'max_attendees', 'venue_id']
        # gets fields which are missing
        missing_items = [key for key in mandatory_input_data if
                         not data.get(key)]
        if missing_items:
            raise EventInputMissing(
                "Mandatory Input Missing: %s" % missing_items)
        EventBase.validate_required_fields(data)

    def event_gt_to_sn_mapping(self, data):
        """
        This is actually the mapping of data from the input data from
        EventCreationForm to the data required for API calls on Meetup.com.
        :param data: dictionary containing event data
        :type data: dict
        :exception KeyError: Can raise KeyError if some key not found in event
                            data.

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

                And then makes Meetup specific data like this

                event_payload = {
                                    'name': 'Test Event',
                                    'social_network_group_id': 18837246,
                                    'group_url_name': 'QC-Python-Learning',
                                    'description': 'Test Event Description',
                                    'time': 14563323434,
                                    'guest_limit': 10
                                }

        """
        assert data, 'Data should not be None/empty'
        assert isinstance(data, dict), 'Data should be a dictionary'
        self.data = data
        self.validate_required_fields(data)
        super(Meetup, self).event_gt_to_sn_mapping(data)
        # converting Datetime object to epoch for API call
        start_time = int(milliseconds_since_epoch_local_time(data['start_datetime']))
        self.payload = {
            'name': data['title'],
            'group_id': data['social_network_group_id'],
            'group_url_name': data['group_url_name'],
            'description': data['description'],
            'time': start_time,
            'guest_limit': data['max_attendees']
        }
        self.venue_id = data['venue_id']
        if data['end_datetime']:
            duration = int((data['end_datetime'] -
                            data['start_datetime']).total_seconds())
            self.payload.update({'duration': duration})
        if data['group_url_name']:
            self.group_url_name = data['group_url_name']
        else:
            error_message = 'Group UrlName for eventName: %s' \
                            % data['title']
            log_error({'user_id': self.user.id,
                       'error': error_message})
        self.social_network_event_id = data.get('social_network_event_id')
