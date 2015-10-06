import json

from datetime import datetime
from datetime import timedelta

from common.models.venue import Venue
from common.models.event import Event
from common.models.organizer import Organizer

from social_network_service.utilities import http_request
from social_network_service.utilities import milliseconds_since_epoch
from social_network_service.utilities import milliseconds_since_epoch_to_dt
from social_network_service.custom_exections import VenueNotFound
from social_network_service.custom_exections import EventNotCreated
from social_network_service.custom_exections import EventInputMissing
from social_network_service.custom_exections import EventLocationNotCreated
from social_network_service.event.base import EventBase
from social_network_service.utilities import log_error
from social_network_service import logger

MEETUP = 'Meetup'


class Meetup(EventBase):
    """
    This class is inherited from TalentEventBase class
    This implements the abstract methods defined in interface
    It also implements functions to create event on Meetup website
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize required class variables to be used later.
        :param args:
        :param kwargs:
        :return:
        """
        super(Meetup, self).__init__(*args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.data = None
        self.payload = None
        self.location = None
        self.group_url_name = None
        self.social_network_event_id = None
        self.start_date = kwargs.get('start_date') or (datetime.now() - timedelta(days=5))
        self.end_date = kwargs.get('end_date') or (datetime.now() + timedelta(days=5))
        self.start_time_since_epoch = milliseconds_since_epoch(self.start_date)
        self.end_time_since_epoch = milliseconds_since_epoch(self.end_date)

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Meetup's API
        does that too.
        :return:
        """
        all_events = []  # contains all events of gt-users
        # page size is 100 so if we have 500 records we will make
        # 5 requests (using pagination where each response will contain
        # 100 records).
        events_url = self.api_url + '/events/?sign=true&page=100&fields=timezone'
        params = {
            'member_id': self.member_id,
            'time': '%.0f, %.0f' %
                    (self.start_time_since_epoch,
                     self.end_time_since_epoch)
        }
        response = http_request('GET', events_url, params=params, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            data = response.json()
            events = []  # contains events on one page
            events.extend(data['results'])
            all_events.extend([event for event in events if
                               self._filter_event(event)])
            # next_url determines the pagination, this variable keeps
            # appearing in response if there are more pages and stops
            # showing when there are no more.
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
        if event['group']['id']:
            url = self.api_url + '/groups/?sign=true'
            response = http_request('GET', url,
                                    params={
                                        'group_id':
                                            event['group']['id']
                                    },
                                    headers=self.headers,
                                    user_id=self.user.id)
            if response.ok:
                group = response.json()
                group_organizer = group['results'][0]['organizer']
                # group_organizer contains a dict that has member_id and name
                if str(group_organizer['member_id']) == self.member_id:
                    return True
        return False

    def event_sn_to_gt_mapping(self, event):
        """
        Basically we take event's data from Meetup's end
        and map their fields to ours and finally we return
        Event's object. We also issue some calls to get updated
        venue and organizer information.
        :param event:
        :return:
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
            # {u'city': u'Cupertino', u'name': u'Meetup Address', u'country': u'US', u'lon': -122.030754,
            #  u'address_1': u'Infinite Loop', u'repinned': False, u'lat': 37.33167, u'id': 24062708}
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
                end_time = milliseconds_since_epoch_to_dt((float(event['time']))
                                                          + (float(end_time) * 1000))

        if group_organizer:
            organizer_data = dict(
                user_id=self.user.id,
                name=group_organizer['name'] if group_organizer.has_key('name') else '',
                email='',
                about=organizer['bio'] if organizer and organizer.has_key('bio') else ''

            )
            organizer_in_db = Organizer.get_by_user_id_and_name(
                self.user.id,
                group_organizer['name'] if group_organizer.has_key('name') else ''
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
                city=venue['city'].title().strip() if venue and venue.has_key('city') else '',
                state=venue['state'].title().strip() if venue and venue.has_key('state') else '',
                zipcode=venue['zip'] if venue and venue.has_key('zip') else None,
                country=venue['country'].title().strip() if venue and venue.has_key('country') else '',
                longitude=float(venue['lon']) if venue and venue.has_key('lon') else 0,
                latitude=float(venue['lat']) if venue and venue.has_key('lat') else 0,
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

        return Event(
            social_network_event_id=event['id'],
            title=event['name'],
            description=event['description'] if event.has_key('description') else '',
            social_network_id=self.social_network.id,
            user_id=self.user.id,
            organizer_id=organizer_id,
            venue_id=venue_id,
            # group id and urlName are required fields to edit an event
            # So, should raise exception if Null
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
                          event.get('yes_rsvp_count', 0) + event.get('waitlist_count', 0)
        )

    def create_event(self):
        """
        This function is used to create meetup event using vendor's API.
        It first creates a draft for event on vendor, then by given address,
        generates venue_id.It then gets the draft, updates the location
        and publishes it (announce). It uses helper functions add_location()
        and publish_meetup().
        """
        url = self.api_url + "/event"
        venue_id = self.add_location()
        self.payload.update({'venue_id': venue_id,
                             'publish_status': 'published'})
        response = http_request('POST', url, params=self.payload, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            event_id = response.json().get('id')
            logger.info('|  Event %s created Successfully  |' % self.payload['name'])
            return event_id, ''
        else:
            error_message = 'Event was not Created. Error occurred during draft creation'
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise EventNotCreated('ApiError: Unable to create event on social network')

    def update_event(self):
        """
        This function is used to create meetup event using vendor's API.
        It first creates a draft for event on vendor, then by given address,
        generates venue_id.It then gets the draft, updates the location
        and publishes it (announce). It uses helper functions add_location()
        and publish_meetup().
        """
        url = self.api_url + "/event/" + str(self.social_network_event_id)
        venue_id = self.add_location()
        self.payload.update({'venue_id': venue_id})
        response = http_request('POST', url, params=self.payload, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            event_id = response.json().get('id')
            logger.info('|  Event %s updated Successfully  |' % self.payload['name'])
            return event_id, ''
        else:
            error_message = 'Event was not Created. Error occurred during event creation on Meetup'
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise EventNotCreated('ApiError: Unable to create event on social network')

    def add_location(self):
        """
        This function adds the location of event for meetup.
        :return: id of venue created if creation is successful.
        """
        venue_in_db = Venue.get_by_user_id_social_network_id_venue_id(self.user.id,
                                                                      self.social_network.id,
                                                                      self.venue_id)
        if venue_in_db:
            if venue_in_db.social_network_venue_id:
                return venue_in_db.social_network_venue_id

            # For creating venue for event, Meetup uses url which is different than
            # the url we use in other API calls of Meetup. So class variable 'api_url' is not
            # used here
            url = 'https://api.meetup.com/' + self.group_url_name + '/venues'
            payload = {
                'address_1': venue_in_db.address_line1,
                'address_2': venue_in_db.address_line2,
                'city': venue_in_db.city,
                'country': venue_in_db.country,
                'state': venue_in_db.state,
                'name': venue_in_db.address_line1
            }
            response = http_request('POST', url, params=payload, headers=self.headers,
                                    user_id=self.user.id)
            if response.ok:
                venue_id = json.loads(response.text)['id']
                logger.info('|  Venue has been Added  |')
            elif response.status_code == 409:
                # 409 is returned when our venue is matching existing venue/venues
                # so we will pick first one in potential matches
                try:
                    venue_id = json.loads(response.text)['errors'][0]['potential_matches'][0]['id']
                    logger.info('|  Venue was picked from matched records  |')
                except Exception as e:
                    raise EventLocationNotCreated('ApiError: Unable to create venue for event',
                                                  detail=str(e))

            else:
                error_message = 'Venue was not Added. There are some errors'
                errors = response.json().get('errors')
                message = '\nErrors from the social network:\n'
                message += '\n'.join(error['message'] + ', ' + error['code'] for error in errors) if errors else ''
                error_message += message
                log_error({'user_id': self.user.id,
                           'error': error_message})
                raise EventLocationNotCreated('ApiError: Unable to create venue for event\n %s' % message)
            venue_in_db.update(social_network_venue_id=venue_id)
            return venue_id
        else:
            error_message = 'Venue does not exist in db. Venue id is %s' % self.venue_id
            log_error({'user_id': self.user.id,
                       'error': error_message})
            raise VenueNotFound('Venue not found in database. Kindly specify a valid venue.')

    def unpublish_event(self, event_id, method='DELETE'):
        """
        This function is used when run unit test. It sets the api_relative_url
        and calls base class method to delete the Event from meetup which was
        created in the unit testing.
        :param event_id:id of newly created event
        :return: True if event is deleted from vendor, False other wsie
        """
        self.url_to_delete_event = self.api_url + "/event/" + str(event_id)
        super(Meetup, self).unpublish_event(event_id, method=method)

    @staticmethod
    def validate_required_fields(data):
        """
        Here we validate that all the required fields for the event creation on
        meetup are filled. If any required filed is missing, raises exception
        named  EventInputMissing.
        """
        mandatory_input_data = ['title', 'description', 'group_id',
                                'group_url_name', 'start_datetime', 'max_attendees',
                                'venue_id']

        if not all([input in data and data[input] for input in mandatory_input_data]):
            log_error({
                'user_id': '',
                'error': 'Mandatory parameters missing in Meetup event data'
            })
            raise EventInputMissing("Mandatory parameter missing in Meetup event data.")

    def event_gt_to_sn_mapping(self, data):
        """
        This is actually the mapping of data from the from to the data required
        for API calls on Meetup.
        """
        if data:
            self.validate_required_fields(data)
            # assert whether data['start_datetime'] is instance of dt
            # converting Datetime object to epoch for API call
            start_time = int(data['start_datetime'].strftime("%s")) * 1000
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
                error_message = 'Group UrlName is None for eventName: %s' % data['title']
                log_error({'user_id': self.user.id,
                           'error': error_message})
            self.social_network_event_id = data.get('social_network_event_id')
            # if self.social_network_event_id:
            #     self.payload.update({'lat': data['latitude'],
            #                          'lon': data['longitude']})
        else:
            error_message = 'Data is None'
            log_error({'user_id': self.user.id,
                       'error': error_message})
