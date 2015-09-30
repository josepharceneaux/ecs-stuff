
import json
from datetime import datetime
from datetime import timedelta
from gt_common.models.event import Event
from gt_common.models.organizer import Organizer
from gt_common.models.venue import Venue
from social_network_service.utilities import http_request, get_message_to_log
from social_network_service.utilities import milliseconds_since_epoch
from social_network_service.utilities import milliseconds_since_epoch_to_dt
from social_network_service.custom_exections import EventNotCreated
from social_network_service.custom_exections import EventNotPublished
from social_network_service.custom_exections import EventNotUnpublished
from social_network_service.custom_exections import EventInputMissing
from social_network_service.custom_exections import EventLocationNotCreated

from social_network_service.event.base import EventBase
from social_network_service.utilities import log_error, logger

MEETUP = 'Meetup'


class MeetupEvent(EventBase):
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
        super(MeetupEvent, self).__init__(*args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.data = None
        self.venue_id = None
        self.payload = None
        self.location = None
        self.group_url_name = None
        self.social_network_event_id = None
        self.start_date = kwargs.get('start_date') or (datetime.now() - timedelta(days=2))
        self.end_date = kwargs.get('end_date') or (datetime.now() + timedelta(days=2))
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
        events_url = self.api_url + '/events/?sign=true&page=100'
        params = {
            'member_id': self.member_id,
            'time': '%.0f, %.0f' %
            (self.start_time_since_epoch,
            self.end_time_since_epoch)
        }
        print 'Params', params
        response = http_request('GET', events_url, params=params, headers=self.headers)
        print 'Response', response
        if response.ok:
            data = response.json()
            print 'Data retrieved'
            print data
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
                response = http_request('GET', url)
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
                                     headers=self.headers)
            if response.ok:
                group = response.json()
                group_organizer = group['results'][0]['organizer']
                # group_organizer contains a dict that has member_id and name
                if str(group_organizer['member_id']) == self.member_id:
                    return True
        return False

    def normalize_event(self, event):
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
        organizer_instance = None
        venue_instance = None
        if event.get('venue'):
            # venue data looks like
            # {u'city': u'Cupertino', u'name': u'Meetup Address', u'country': u'US', u'lon': -122.030754,
                #  u'address_1': u'Infinite Loop', u'repinned': False, u'lat': 37.33167, u'id': 24062708}
            venue = event['venue']

        print 'Venue', venue
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
                         headers=self.headers
            )
            if response.ok:
                group = response.json()
                print 'Group', group
                if group.has_key('results'):
                    # contains a dict that has member_id and name
                    # Organizer data looks like
                    # { u'name': u'Waqas Younas', u'member_id': 183366764}
                    group_organizer = group['results'][0]['organizer']
                    url = self.api_url + '/member/' + \
                          str(group_organizer['member_id']) + '?sign=true'
                    response = http_request('GET', url, headers=self.headers)
                    if response.ok:
                        organizer = response.json()
                    print "organizer", organizer
            start_time = milliseconds_since_epoch_to_dt(float(event['time']))
            end_time = event['duration'] if event.has_key('duration') else None
            if end_time:
                end_time = milliseconds_since_epoch_to_dt((float(event['time']))
                                                          + (float(end_time) * 1000))

        if group_organizer:
            organizer_instance = Organizer(
                user_id=self.user.id,
                name=group_organizer['name'] if group_organizer.has_key('name') else '',
                email='',
                about=organizer['bio'] if organizer and organizer.has_key('bio') else ''

            )
            Organizer.save(organizer_instance)
        if venue:
            venue_instance = Venue(
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
            Venue.save(venue_instance)

        return Event(
<<<<<<< HEAD
            social_network_event_id=event['id'],
=======
            id=event['id'],
>>>>>>> 0774d2b3242d0ae975f49c99c0b0b53b8994cef5
            title=event['name'],
            description=event['description'] if event.has_key('description') else '',
            social_network_id=self.social_network.id,
            user_id=self.user.id,
            organizer_id = organizer_instance.id if organizer_instance else None,
            venue_id = venue_instance.id if venue_instance else None,
            # group id and urlName are required fields to edit an event
            # So, should raise exception if Null
            group_id=event['group']['id'] if event.has_key('group') else '',
            group_url_name=event['group']['urlname'],
            # Let's drop error logs if venue has no address, or if address
            # has no longitude/latitude
            url='',
            start_datetime=start_time,
            end_datetime=end_time,
            registration_instruction='',
            cost=0,
            currency='',
            timezone='',
            max_attendees=0
        )

    def create_event(self):
        """
        This function is used to create meetup event using vendor's API.
        It first creates a draft for event on vendor, then by given address,
        generates venue_id.It then gets the draft, updates the location
        and publishes it (announce). It uses helper functions add_location()
        and publish_meetup().
        """
        if self.social_network_event_id is not None:
            url = self.api_url + "/event/" + str(self.social_network_event_id)
            event_is_new = False
        else:
            url = self.api_url + "/event"
            event_is_new = True
        response = http_request('POST', url, params=self.payload, headers=self.headers)
        if response.ok:
            event_id = response.json().get('id')
            create_update = 'Created' if not self.social_network_event_id else 'Updated'
            venue_id = self.add_location()
            self.publish_meetup(venue_id, event_id, event_is_new)
            logger.info('|  Event %s %s Successfully  |'
                        % (self.payload['name'], create_update))
            return event_id, ''
        else:
            error_message = 'Event was not Created. Error occurred during draft creation'

            message_to_log = get_message_to_log(function_name='create_event',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=error_message,
                                                file_name=__file__)
            log_error(message_to_log)
            raise EventNotCreated('ApiError: Unable to create event on social network')

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

    def add_location(self):
        """
        This function adds the location of event for meetup.
        :return: id of venue created if creation is successful.
        """
        # For deleting an event, Meetup uses url which is different than
        # the url we use in other API calls of Meetup. So class variable 'api_url' is not
        # used here
        venue = Venue.get_by_id(self.venue_id)
        assert venue is not None, 'Unable to found venue for given id'
        url = 'https://api.meetup.com/' + self.group_url_name + '/venues'
        payload = {
            'address_1': venue.address_line1,
            'address_2': venue.address_line2,
            'city': venue.city,
            'country': venue.country,
            'state': venue.state,
            'name': "Meetup Address"
        }
        response = http_request('POST', url, params=payload, headers=self.headers)
        if response.ok:
            venue_id = json.loads(response.text)['id']
            logger.info('|  Venue has been Added  |')
        elif response.status_code == 409:
            venue_id = json.loads(response.text)['errors'][0]['potential_matches'][0]['id']
            logger.info('|  Venue was picked from matched records  |')
        else:
            error_message = 'Venue was not Added. There are some errors'
            errors = response.json().get('errors')
            message = '\nErrors from the social network:\n'
            message += '\n'.join(error['message'] + ', ' + error['code'] for error in errors) if errors else ''
            error_message += message
            message_to_log = get_message_to_log(function_name='add_location',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=error_message,
                                                file_name=__file__)
            log_error(message_to_log)
            raise EventLocationNotCreated('ApiError: Unable to create venue for event\n %s' % message)
        return venue_id

    def publish_meetup(self, venue_id, event_id, event_is_new):
        """
        Here we publish the event on Meetup website.
        :param venue_id: id of venue to update location of event
        :param event_id: id of newly created event
        :param event_is_new: determines if creating, editing the event
        :return: True if event has updated and published successfully,
        False otherwise
        """
        # create url to publish event
        url = self.api_url + "/event/" + event_id
        payload = {'venue_id': venue_id}
        # if we are Creating the event, then announce this event
        # else assuming event is already announced, just updating data
        payload.update({'announce': True}) if event_is_new else ''
        response = http_request('POST', url, params=payload, headers=self.headers)
        if response.ok:
            logger.info('|  Event has been published  |')
            return True
        else:
            error_message = 'Event was not published'
            message_to_log = get_message_to_log(function_name='publish_meetup',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=error_message,
                                                file_name=__file__)
            log_error(message_to_log)
            raise EventNotPublished('ApiError: Unable to publish event on specified social network')

    def unpublish_event(self, event_id):
        """
        This function is used when run unit test. It deletes the Event from
        meetup which was created in the unit testing.
        :param event_id:id of newly created event
        :return: True if event is deleted from vendor, False other wsie
        """
        # create url to publish event
        url = self.api_url + "/event/" + event_id
        # params are None. Access token is present in self.headers
        response = http_request('POST', url, headers=self.headers)
        if response.ok:
            logger.info('|  Event has been unpublished (deleted)  |')
        else:
            error_message = "Event was not unpublished (deleted)."
            message_to_log = get_message_to_log(function_name='unpublish_event',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=error_message,
                                                file_name=__file__)
            log_error(message_to_log)
            raise EventNotUnpublished('ApiError: Unable to remove event from specified social network')

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
            raise EventInputMissing("Mandatory parameter missing in Meetup event data.")

    def gt_to_sn_fields_mappings(self, data):
        """
        This is actually the mapping of data from the from to the data required
        for API calls on Meetup.
        """
        if data:
            self.validate_required_fields(data)
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
                message_to_log = get_message_to_log(function_name='gt_to_sn_fields_mappings',
                                                    class_name=self.__class__.__name__,
                                                    gt_user=self.user.name,
                                                    error=error_message,
                                                    file_name=__file__)
                log_error(message_to_log)
            self.social_network_event_id = data.get('social_network_event_id')
            # if self.social_network_event_id:
            #     self.payload.update({'lat': data['latitude'],
            #                          'lon': data['longitude']})
        else:
            error_message = 'Data is None'
            message_to_log = get_message_to_log(function_name='gt_to_sn_fields_mappings',
                                                class_name=self.__class__.__name__,
                                                gt_user=self.user.name,
                                                error=error_message,
                                                file_name=__file__)
            log_error(message_to_log)

