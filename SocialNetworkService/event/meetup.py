from datetime import datetime
from datetime import timedelta
from gt_common.gt_models.event import Event
from SocialNetworkService.utilities import http_request
from SocialNetworkService.utilities import milliseconds_since_epoch
from SocialNetworkService.utilities import milliseconds_since_epoch_to_dt
from base import EventBase


class Meetup(EventBase):

    def __init__(self, *args, **kwargs):
        super(Meetup, self).__init__(*args, **kwargs)
        self.start_date = kwargs.get('start_date') or (datetime.now() - timedelta(days=2))
        self.end_date = kwargs.get('end_date') or (datetime.now() + timedelta(days=2))
        self.start_time_since_epoch = milliseconds_since_epoch(self.start_date)
        self.end_time_since_epoch = milliseconds_since_epoch(self.end_date)
        self.headers = {
            'Authorization': 'Bearer %s' % self.access_token
        }
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
        return Event(
            vendorEventId=event['id'],
            eventTitle=event['name'],
            eventDescription=event['description'] if event.has_key('description') else '',
            socialNetworkId=self.social_network.id,
            userId=self.user.id,

            # group id and urlName are required fields to edit an event
            # So, should raise exception if Null
            groupId=event['group']['id'],
            groupUrlName=event['group']['urlname'],
            # Let's drop error logs if venue has no address, or if address
            # has no longitude/latitude
            eventAddressLine1=venue['address_1'] if venue else '',
            eventAddressLine2='',
            eventCity=venue['city'].title() if venue else '',
            eventState=venue['state'] if venue and venue.has_key('state') else '',
            eventZipCode=venue['zip'] if venue and venue.has_key('zip') else '',
            eventCountry=venue['country'] if venue and venue.has_key('country') else '',
            eventLongitude=float(venue['lon']) if venue and venue.has_key('lon') else 0,
            eventLatitude=float(venue['lat']) if venue and venue.has_key('lat') else 0,
            eventStartDateTime=start_time,
            eventEndDateTime=end_time,
            organizerName=group_organizer['name'] if group_organizer and group_organizer.has_key('name') else '',
            organizerEmail='',
            aboutEventOrganizer=organizer['bio'] if organizer and organizer.has_key('bio') else '',
            registrationInstruction='',
            eventCost='',
            eventCurrency='',
            eventTimeZone='',
            maxAttendees=0
        )
