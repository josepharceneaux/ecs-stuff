import json
from base import EventBase
from datetime import datetime
from datetime import timedelta
from gt_common.gt_models.event import Event
from SocialNetworkService.utilities import http_request

class Eventbrite(EventBase):

    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)
        self.start_date_in_utc = kwargs.get('start_date') or \
            (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.headers = {
            'Authorization': 'Bearer %s' % self.access_token
        }
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
                    vendorEventId=event['id'],
                    eventTitle=event['name']['text'],
                    eventDescription=event['description']['text'],
                    socialNetworkId=self.social_network.id,
                    userId=self.user.id,
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
                return event_db
        else:
            # TODO log exception here
            pass # log exception