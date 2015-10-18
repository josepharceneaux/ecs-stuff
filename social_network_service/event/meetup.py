"""
This modules contains Meetup class. It inherits from EventBase class.
Meetup contains methods to create, update, get, delete events.
It also contains methods to get RSVPs of events.
"""

# Standard Library
import json
from datetime import datetime
from datetime import timedelta

# Application specific
from common.models.venue import Venue
from common.models.event import Event
from common.models.organizer import Organizer
from social_network_service import logger
from social_network_service.event.base import EventBase
from social_network_service.utilities import http_request
from social_network_service.utilities import milliseconds_since_epoch
from social_network_service.utilities import milliseconds_since_epoch_to_dt
from social_network_service.utilities import log_error
from social_network_service.custom_exections import VenueNotFound
from social_network_service.custom_exections import EventNotCreated
from social_network_service.custom_exections import EventInputMissing
from social_network_service.custom_exections import EventLocationNotCreated


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
            - url_to_delete_event:
                URL to unpublist event from social network (Meetup)
            - member_id:
                user member id on Meetup
            - venue_id:
                Id of the location for this event
            - payload:
                a dictionary containing data for event creation on Meetup
            - group_url_name:
                Meetup group name owned by this user
            - group_ids:
                list of group ids owned by user
            - social_network_event_id:
                event id of event on Meetup
            - start_time_since_epoch:
                time passed after epoch till start_time
            - end_time_since_epoch:
                time passed after epoch till end_time

        :param args:
        :param kwargs:
        :return:
        """
        super(Meetup, self).__init__(*args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.data = None
        self.payload = None
        self.group_url_name = None
        self.group_ids = []
        self.social_network_event_id = None
        self.start_date = kwargs.get('start_date') \
                          or (datetime.now() + timedelta(days=19))
        self.end_date = kwargs.get('end_date') \
                        or (datetime.now() + timedelta(days=23))
        self.start_time_since_epoch = milliseconds_since_epoch(self.start_date)
        self.end_time_since_epoch = milliseconds_since_epoch(self.end_date)

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Meetup's API
        does that too.
        :return: all_events: list of events retrieved from Meetup.com
        :rtype all_events: list
        """
        all_events = []  # contains all events of gt-users
        # page size is 100 so if we have 500 records we will make
        # 5 requests (using pagination where each response will contain
        # 100 records).
        events_url = \
            self.api_url + '/events/?sign=true&page=100&fields=timezone'
        params = {
            'member_id': self.member_id,
            'time': '%.0f, %.0f' %
                    (self.start_time_since_epoch,
                     self.end_time_since_epoch)
        }
        response = http_request('GET', events_url, params=params,
                                headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            data = response.json()
            events = []  # contains events on one page
            events.extend(data['results'])
            all_events.extend([event for event in events if
                               self._filter_event(event)])
            # next_url determines the pagination, this variable keeps
            # appearing in response if there are more pages and stops
            # showing up when there are no more.
            next_url = data['meta']['next'] or None
            while next_url:
                events = []  # resetting events for next page
                # attach the key before sending the request
                url = next_url + '&sign=true'
                response = http_request('GET', url, headers=self.headers,
                                        user_id=self.user.id)
                if response.ok:
                    data = response.json()
                    events.extend(data['results'])
                    all_events.extend([event for event in events if
                                       self._filter_event(event)])
                    next_url = data['meta']['next'] or None
                    if not next_url:
                        break
                else:
                    all_events.extend([])
        return all_events

    def _filter_event(self, event):
        """
        This method returns True if given event's group is owned by current user.
        :param event: event to be tested
        :type event: dict
        :return True or False
        :rtype Boolean
        """
        group_id = event['group'].get('id')
        # check if event's group id exists
        if group_id:
            if group_id in self.group_ids:
                return True
            url = self.api_url + '/groups/?sign=true'
            response = http_request('GET', url,
                                    params={
                                        'group_id': group_id
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
                    self.group_ids.append(group_id)
                    return True
        return False

    def event_sn_to_gt_mapping(self, event):
        """
        We take event's data from social network's API and map its fields to
        getTalent database fields. Finally we return Event's object to
        save/update record in getTalent database.
        We also issue some calls to get updated venue and organizer information.
        :param event: data from Meetup's API.
        :type event: dictionary
        :exception Exception: It raises exception if there is an error getting
            data from API.
        :return: event: Event object
        :rtype event: common.models.event.Event
        """
        organizer = None
        venue = None
        group_organizer = None
        organizer_id = None
        venue_id = None
        start_time = None
        end_time = None
        if event.get('venue'):
            # venue data looks like
            # {
            #       u'city': u'Cupertino', u'name': u'Meetup Address',
            #       u'country': u'US', u'lon': -122.030754,
            #       u'address_1': u'Infinite Loop', u'repinned': False,
            #       u'lat': 37.33167, u'id': 24062708
            # }
            venue = event['venue']
        # Get organizer info. First get the organizer from group info and
        # then get organizer's information which will be used to store
        # in the event.

        if event.has_key('group') and \
                event['group'].has_key('id'):

            url = self.api_url + '/groups/?sign=true'
            response = http_request('GET', url,
                                    params={
                                        'group_id': event['group']['id']
                                    },
                                    headers=self.headers,
                                    user_id=self.user.id
                                    )
            if response.ok:
                group = response.json()
                if group.has_key('results'):
                    # contains a dict that has member_id and name
                    # Organizer data looks like
                    # { u'name': u'Waqas Younas', u'member_id': 183366764}
                    group_organizer = group['results'][0]['organizer']
                    url = self.api_url + '/member/' + \
                          str(group_organizer['member_id']) + '?sign=true'
                    response = http_request('GET', url, headers=self.headers,
                                            user_id=self.user.id)
                    if response.ok:
                        organizer = response.json()
            start_time = milliseconds_since_epoch_to_dt(float(event['time']))
            end_time = event['duration'] if event.has_key('duration') else None
            if end_time:
                end_time = \
                    milliseconds_since_epoch_to_dt(
                        (float(event['time'])) + (float(end_time) * 1000))

        if group_organizer:
            organizer_data = dict(
                user_id=self.user.id,
                name=group_organizer['name']
                if group_organizer.has_key('name') else '',
                email='',
                about=organizer['bio']
                if organizer and organizer.has_key('bio') else ''

            )
            organizer_in_db = Organizer.get_by_user_id_and_name(
                self.user.id,
                group_organizer['name'] if group_organizer.has_key(
                    'name') else ''
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
                social_network_venue_id=venue['id'],
                user_id=self.user.id,
                address_line1=venue['address_1'] if venue else '',
                address_line2='',
                city=venue['city'].title().strip()
                if venue and venue.has_key('city') else '',
                state=venue['state'].title().strip()
                if venue and venue.has_key('state') else '',
                zipcode=venue['zip']
                if venue and venue.has_key('zip') else None,
                country=venue['country'].title().strip()
                if venue and venue.has_key('country') else '',
                longitude=float(venue['lon'])
                if venue and venue.has_key('lon') else 0,
                latitude=float(venue['lat'])
                if venue and venue.has_key('lat') else 0,
            )
            venue_in_db = Venue.get_by_user_id_and_social_network_venue_id(
                self.user.id, venue['id'])
            if venue_in_db:
                venue_in_db.update(**venue_data)
                venue_id = venue_in_db.id
            else:
                venue = Venue(**venue_data)
                Venue.save(venue)
                venue_id = venue.id

        return Event(
            social_network_event_id=event['id'],
            title=event['name'],
            description=event['description']
            if event.has_key('description') else '',
            social_network_id=self.social_network.id,
            user_id=self.user.id,
            organizer_id=organizer_id,
            venue_id=venue_id,
            # group id and urlName are required fields to edit an event
            # so should raise exception if Null
            group_id=event['group']['id'] if event.has_key('group') else '',
            group_url_name=event['group']['urlname'],
            # Let's drop error logs if venue has no address, or if address
            # has no longitude/latitude
            url=event['event_url'],
            start_datetime=start_time,
            end_datetime=end_time,
            registration_instruction='',
            cost=0,
            currency='',
            timezone=event.get('timezone'),
            max_attendees=event.get('maybe_rsvp_count', 0) +
                          event.get('yes_rsvp_count', 0) +
                          event.get('waitlist_count', 0)
        )

    def create_event(self):
        """
        This function is used to create Meetup event using vendor's API.
        It first creates a venue for event. Then venue_id is passed to
        event_payload.
        Then a POST request to Meetup API creates event on Meetup.com
        :exception EventNotCreated: raises exception if unable to
        publish/create event on Meetup.com.
        """
        url = self.api_url + "/event"
        venue_id = self.add_location()
        self.payload.update({'venue_id': venue_id,
                             'publish_status': 'published'})
        response = http_request('POST', url, params=self.payload,
                                headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            event_id = response.json().get('id')
            logger.info('|  Event %s created Successfully  |'
                        % self.payload['name'])
            self.data['social_network_event_id'] = event_id
            return self.save_event()
        else:
            error_message = 'Event was not Created. Error occurred during' \
                            ' draft creation'
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise EventNotCreated('ApiError: Unable to create event on Meetup')

    def update_event(self):
        """
        It first creates/ updates a venue on Meetup.com and then passes that
        venue's id in event's payload to update event location along with event
        data.
        :exception EventNotCreated: raises exception if unable to update event
                on Meetup.com
        :return
        """
        # create url to update event
        url = self.api_url + "/event/" + str(self.social_network_event_id)
        # create or update venue for event
        venue_id = self.add_location()
        # add venue id in event payload to update event venue on Meetup.com
        self.payload.update({'venue_id': venue_id})
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
        if venue_in_db:
            if venue_in_db.social_network_venue_id:
                return venue_in_db.social_network_venue_id

            # For creating venue for event, Meetup uses url which is
            # different than the url we use in other API calls of Meetup.
            # So class variable 'api_url' is not used here.
            url = 'https://api.meetup.com/' + self.group_url_name + '/venues'
            payload = {
                'address_1': venue_in_db.address_line1,
                'address_2': venue_in_db.address_line2,
                'city': venue_in_db.city,
                'country': venue_in_db.country,
                'state': venue_in_db.state,
                'name': venue_in_db.address_line1
            }
            response = http_request('POST', url, params=payload,
                                    headers=self.headers,
                                    user_id=self.user.id)
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
                    raise EventLocationNotCreated('ApiError: Unable to create'
                                                  ' venue for event',
                                                  additional_error_info=
                                                  dict(venue_error=str(e)))
            else:
                error_message = 'Venue was not Added. There are some errors.'
                errors = response.json().get('errors')
                message = '\nErrors from the social network:\n'
                message += '\n'.join(error['message'] + ', ' + error['code']
                                     for error in errors) if errors else ''
                error_message += message
                log_error({'user_id': self.user.id,
                           'error': error_message})
                raise EventLocationNotCreated('ApiError: Unable to create '
                                              'venue for event\n %s' % message)
            venue_in_db.update(social_network_venue_id=venue_id)
            return venue_id
        else:
            error_message = 'Venue does not exist in db. Venue id is %s' \
                            % self.venue_id
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise VenueNotFound('Venue not found in database. Kindly specify '
                                'a valid venue.')

    def unpublish_event(self, social_network_event_id, method='DELETE'):
        """
        This function is used while running unit test. It sets the api_relative_url
        and calls base class method to delete the Event from Meetup which was
        created in the unit test.
        :param social_network_event_id:id of newly created event
        :type social_network_event_id: int
        :return: True if event is deleted from vendor, False otherwise.
        :rtype Boolean
        """
        self.url_to_delete_event = self.api_url + "/event/" \
                                   + str(social_network_event_id)
        super(Meetup, self).unpublish_event(social_network_event_id,
                                            method=method)

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
        mandatory_input_data = ['title', 'description', 'group_id',
                                'group_url_name', 'start_datetime',
                                'max_attendees',
                                'venue_id']
        # gets fields which are missing
        missing_items = [key for key in mandatory_input_data if
                         not data.get(key)]
        if missing_items:
            raise EventInputMissing(
                "Mandatory Input Missing: %s" % missing_items)

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
                        "group_id": 18837246,
                        "max_attendees": 10
                }

                And then makes Meetup specific data like this

                event_payload = {
                                    'name': 'Test Event',
                                    'group_id': 18837246,
                                    'group_url_name': 'QC-Python-Learning',
                                    'description': 'Test Event Description',
                                    'time': 14563323434,
                                    'guest_limit': 10
                                }

        """
        assert data, 'Data should not be None/empty'
        assert isinstance(data, dict), 'Data should be a dictionary'
        super(Meetup, self).event_gt_to_sn_mapping(data)
        self.data = data
        self.validate_required_fields(data)
        # assert whether data['start_datetime'] is instance of dt
        # converting Datetime object to epoch for API call
        start_time = int(milliseconds_since_epoch(data['start_datetime']))
        self.payload = {
            'name': data['title'],
            'group_id': data['group_id'],
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
            error_message = 'Group UrlName is None for eventName: %s' \
                            % data['title']
            log_error({'user_id': self.user.id,
                       'error': error_message})
        self.social_network_event_id = data.get('social_network_event_id')
