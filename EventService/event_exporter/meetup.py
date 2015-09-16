import json
from event_manager import logger
from event_exporter.publish.base import TalentEventBase
from event_exporter.publish.common import _log_error, EventNotCreated, EventLocationNotCreated, EventNotPublished, \
    EventNotUnpublished, EventInputMissing

MEETUP = 'Meetup'


class Meetup(TalentEventBase):
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
        super(Meetup, self).__init__(MEETUP, *args, **kwargs)
        # calling super constructor sets the api_url and access_token
        self.data = None
        self.payload = None
        self.location = None
        self.group_url_name = None
        self.vendor_event_id = None
        self.message_to_log.update({'class': MEETUP})

    def create_event(self):
        """
        This function is used to create meetup event using vendor's API.
        It first creates a draft for event on vendor, then by given address,
        generates venue_id.It then gets the draft, updates the location
        and publishes it (announce). It uses helper functions add_location()
        and publish_meetup().
        """
        self.message_to_log.update({'functionName': 'create_event()'})
        if self.vendor_event_id is not None:
            url = self.api_url + "/event/" + str(self.vendor_event_id)
            event_is_new = False
        else:
            url = self.api_url + "/event"
            event_is_new = True
        response = self.post_data(url, self.payload)
        if response.ok:
            event_id = response.json().get('id')
            create_update = 'Created' if not self.vendor_event_id else 'Updated'
            venue_id = self.add_location()
            self.publish_meetup(venue_id, event_id, event_is_new)
            logger.info('|  Event %s %s Successfully  |'
                        % (self.payload['name'], create_update))
            return event_id, ''
        else:
            error_message = 'Event was not Created. Error occurred during draft creation'
            self.message_to_log.update({'error': error_message})
            _log_error(self.message_to_log)
            raise EventNotCreated

    def add_location(self):
        """
        This function adds the location of event for meetup.
        :return: id of venue created if creation is successful.
        """
        # For deleting an event, Meetup uses url which is different than
        # the url we use in other API calls of Meetup. So class variable 'api_url' is not
        # used here
        self.message_to_log.update({'functionName': 'add_location()'})
        url = 'https://api.meetup.com/' + self.group_url_name + '/venues'
        payload = {
            'address_1': self.payload['address_1'],
            'address_2': self.payload['address_2'],
            'city': self.payload['city'],
            'country': self.payload['country'],
            'state': self.payload['state'],
            'name': "Meetup Address"
        }
        response = self.post_data(url, payload)
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
            self.message_to_log.update({'error': error_message})
            _log_error(self.message_to_log)
            raise EventLocationNotCreated(message)
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
        self.message_to_log.update({'functionName': 'publish_meetup()'})
        # create url to publish event
        url = self.api_url + "/event/" + event_id
        payload = {'venue_id': venue_id}
        # if we are Creating the event, then announce this event
        # else assuming event is already announced, just updating data
        payload.update({'announce': True}) if event_is_new else ''
        response = self.post_data(url, payload)
        if response.ok:
            logger.info('|  Event has been published  |')
            return True
        else:
            error_message = 'Event was not published'
            self.message_to_log.update({'error': error_message})
            _log_error(self.message_to_log)
            raise EventNotPublished

    def unpublish_event(self, event_id):
        """
        This function is used when run unit test. It deletes the Event from
        meetup which was created in the unit testing.
        :param event_id:id of newly created event
        :return: True if event is deleted from vendor, False other wsie
        """
        self.message_to_log.update({'functionName': 'unpublish_event()'})
        # create url to publish event
        url = self.api_url + "/event/" + event_id
        # params are None. Access token is present in self.headers
        response = self.post_data(url, None)
        if response.ok:
            logger.info('|  Event has been unpublished (deleted)  |')
        else:
            error_message = "Event was not unpublished (deleted)."
            self.message_to_log.update({'error': error_message})
            _log_error(self.message_to_log)
            raise EventNotUnpublished

    def get_groups(self):
        """
        This function returns the groups of Meetup for which the current user
        is an organizer to be shown in drop down while creating event on Meetup
        through Event Creation Form.
        """
        self.message_to_log.update({'functionName': 'get_groups()'})
        url = self.api_url + '/groups/'
        params = {'member_id': 'self'}
        response = self.get_data(url, params)
        if response.ok:
            meta_data = json.loads(response.text)['meta']
            member_id = meta_data['url'].split('=')[1].split('&')[0]
            data = json.loads(response.text)['results']
            groups = filter(lambda item: item['organizer']['member_id'] == int(member_id), data)
            return groups

    def validate_required_fields(self, data):
        """
        Here we validate that all the required fields for the event creation on
        meetup are filled. If any required filed is missing, raises exception
        named  EventInputMissing.
        """
        mandatory_input_data = ['eventTitle', 'eventDescription', 'groupId',
                                'groupUrlName', 'eventStartDatetime', 'maxAttendees',
                                'eventAddressLine1',
                                'eventCountry', 'eventState', 'eventZipCode']

        if not all([input in data for input in mandatory_input_data]):
            raise EventInputMissing("Mandatory parameter missing in Meetup call.")

    def get_mapped_data(self, data):
        """
        This is actually the mapping of data from the from to the data required
        for API calls on Meetup.
        """
        self.message_to_log.update({'functionName': 'get_mapped_data()'})
        if data:
            self.validate_required_fields(data)
            # converting Datetime object to epoch for API call
            start_time = int(data['eventStartDatetime'].strftime("%s")) * 1000
            self.payload = {
                'name': data['eventTitle'],
                'group_id': data['groupId'],
                'group_urlname': data['groupUrlName'],
                'description': data['eventDescription'],
                'time': start_time,
                'guest_limit': data['maxAttendees'],
                'address_1': data['eventAddressLine1'],
                'address_2': data['eventAddressLine2'],
                'city': data['eventCity'],
                'country': data['eventCountry'],
                'state': data['eventState']
            }
            if data['eventEndDatetime']:
                duration = int((data['eventEndDatetime'] -
                                data['eventStartDatetime']).total_seconds())
                self.payload.update({'duration': duration})
            if data['groupUrlName']:
                self.group_url_name = data['groupUrlName']
            else:
                error_message = 'Group UrlName is None for eventName: %s' % data['eventTitle']
                self.message_to_log.update({'error': error_message})
                _log_error(self.message_to_log)
            self.vendor_event_id = data.get('vendorEventId')
            if self.vendor_event_id:
                self.payload.update({'lat': data['eventLatitude'],
                                     'lon': data['eventLongitude']})
        else:
            error_message = 'Data is None'
            self.message_to_log.update({'error': error_message})
            _log_error(self.message_to_log)