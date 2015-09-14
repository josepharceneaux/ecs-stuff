"""
This class gets us events for Meetup within a specified day time window.
It inherits from Base and overrides get_events() and normalize_event()
"""
from datetime import datetime, timedelta
import requests
from base import Base
from gt_models.user import UserCredentials
from utilities import milliseconds_since_epoch, \
    milliseconds_since_epoch_to_dt, Attendee, log_exception, log_error
from gt_models.event import Event


class Meetup(Base):
    def __init__(self, *args, **kwargs):
        super(Meetup, self).__init__(*args, **kwargs)
        self.start_date = kwargs.get('start_date') or (datetime.now() - timedelta(days=90))
        self.end_date = kwargs.get('end_date') or (datetime.now() + timedelta(days=90))
        self.start_time_since_epoch = milliseconds_since_epoch(self.start_date)
        self.end_time_since_epoch = milliseconds_since_epoch(self.end_date)
        self.start_date_dt = self.start_date
        self.end_date_dt = self.end_date
        self.vendor = 'Meetup'

    def token_validity(self, access_token):
        header = {'Authorization': 'Bearer ' + access_token}
        result = requests.post(self.api_url + "/member/self", headers=header)
        if result.ok:
            return True
        else:
            return False

    def refresh_token(self):
        status = False
        user_refresh_token = self.user_credential.refreshToken
        auth_url = self.user_credential.social_network.authUrl + "/access?"
        client_id = self.user_credential.social_network.clientKey
        client_secret = self.user_credential.social_network.secretKey
        payload_data = {'client_id': client_id,
                        'client_secret': client_secret,
                        'grant_type': 'refresh_token',
                        'refresh_token': user_refresh_token}
        response = requests.post(auth_url, data=payload_data)
        if response.ok:
            try:
                access_token = response.json()['access_token']
                token_updated_in_db = \
                    UserCredentials.update_auth_token(self.gt_user_id,
                                                      self.social_network_id,
                                                      access_token)
                if token_updated_in_db:
                    return access_token
                else:
                    log_error(self.traceback_info,
                              "Error occurred while saving fresh token of Meetup")
            except Exception as e:
                log_exception(self.traceback_info,
                              "Error occurred while refreshing token" + e.message)
        else:
            log_error(self.traceback_info, response.json()['error'])
        return status

    def get_events(self):
        """
        We send GET requests to API URL and get data. We also
        have to handle pagination because Meetup's API
        does that too.
        :return:
        """
        self.traceback_info.update({"functionName": "get_events()"})
        all_events = []  # contains all events of gt-users
        # page size is 100 so if we have 500 records we will make
        # 5 requests (using pagination where each response will contain
        # 100 records).
        events_url = self.api_url + '/events/?sign=true&page=100'
        params = {'member_id': self.member_id,
                  'time': '%.0f, %.0f' %
                  (self.start_time_since_epoch,
                   self.end_time_since_epoch)}
        response = self.http_get(events_url, params=params)
        if response.ok:
            try:
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
                    response = self.http_get(url)
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
            except Exception as e:
                log_exception(self.traceback_info, e.message)
        return all_events

    def _filter_event(self, event):
        self.traceback_info.update({"functionName": "_filter_event()"})
        try:
            if event['group']['id']:
                url = self.api_url + '/groups/?sign=true'
                response = self.http_get(url,
                                         params=
                                         {'group_id':
                                         event['group']['id']},)
                if response.ok:
                    group = response.json()
                    group_organizer = group['results'][0]['organizer']
                    # group_organizer contains a dict that has member_id and name
                    if str(group_organizer['member_id']) == self.member_id:
                        return True
        except Exception as e:
            log_exception(self.traceback_info, e.message)
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
        self.traceback_info.update({"functionName": "normalize_event()"})
        if event.get('venue'):
            venue = event['venue']
            # get organizer information
            try:
                url = self.api_url + '/groups/?sign=true'
                response = self.http_get(url,
                                         params={
                                             'group_id': event['group']['id']})
                if response.ok:
                    group = response.json()
                    # contains a dict that has member_id and name
                    group_organizer = group['results'][0]['organizer']
                    url = self.api_url + '/member/' + \
                          str(group_organizer['member_id']) + '?sign=true'
                    response = self.http_get(url)
                    if response.ok:
                        organizer = response.json()
                start_time = milliseconds_since_epoch_to_dt(float(event['time']))
                end_time = event['duration'] if event.has_key('duration') else None
                if end_time:
                    end_time = milliseconds_since_epoch_to_dt((float(event['time']))
                                                              + (float(end_time) * 1000))
                return Event(
                    vendorEventId=event['id'],
                    eventTitle=event['name'],
                    eventDescription=event['description'] if event.has_key('description') else '',
                    socialNetworkId=self.social_network_id,
                    userId=self.gt_user_id,

                    # group id and urlName are required fields to edit an event
                    # So, should raise exception if Null
                    groupId=event['group']['id'],
                    groupUrlName=event['group']['urlname'],
                    # Let's drop error logs if venue has no address, or if address
                    # has no longitude/latitude
                    eventAddressLine1=venue['address_1'],
                    eventAddressLine2='',
                    eventCity=venue['city'].title(),
                    eventState=venue.get('state', ''),
                    eventZipCode=venue.get('zip', ''),
                    eventCountry=venue['country'],
                    eventLongitude=float(venue['lon']),
                    eventLatitude=float(venue['lat']),
                    eventStartDateTime=start_time,
                    eventEndDateTime=end_time,
                    organizerName=group_organizer['name'] if group_organizer else '',
                    organizerEmail='',
                    aboutEventOrganizer=organizer['bio'] if organizer.has_key('bio') else '',
                    registrationInstruction='',
                    eventCost='',
                    eventCurrency='',
                    eventTimeZone='',
                    maxAttendees=0)
            except Exception as e:
                event['error_message'] = e.message
                log_exception(self.traceback_info,
                              "Couldn't normalize event. "
                              "eventName: %(name)s, "
                              "eventId on Vendor:%(id)s, "
                              "error_message: %(error_message)s, "
                              % event)
        else:
            log_error(self.traceback_info,
                      "Couldn't normalize event because it has no Venue."
                      " eventName:%(name)s,"
                      " eventId on Vendor:%(id)s, " % event)

    def get_rsvps(self, event):
        self.traceback_info.update({"functionName": "get_rsvps()"})
        rsvps = []
        social_network_id = event.socialNetworkId
        assert social_network_id is not None
        events_url = self.api_url + '/rsvps/?sign=true&page=100'
        params = {'event_id': event.vendorEventId}
        response = self.http_get(events_url, params=params)
        if response.ok:
            data = response.json()
            rsvps.extend(data['results'])
            # next_url determines the pagination, this variable keeps
            # appearing in response if there are more pages and stops
            # showing when there are no more. We have almost the same
            # code for events' pagination, might consolidate it.
            next_url = data['meta']['next'] or None
            while next_url:
                # attach the key before sending the request
                response = self.http_get(next_url + '&sign=true')
                if response.ok:
                    data = response.json()
                    rsvps.extend(data['results'])
                    next_url = data['meta']['next'] or None
                    if not next_url:
                        break
            return rsvps
        elif response.status_code == 401:
            # This is the error code for Not Authorized user(Expired Token)
            # if this error code occurs, we return None and RSVPs are not
            # processed further
            return None

    def get_attendee(self, rsvp):
        """
        RSVP data return from Meetup looks like
        {
                'group': {
                    'group_lat': 24.860000610351562, 'created': 1439953915212, 'join_mode': 'open', 'group_lon': 67.01000213623047, 'urlname': 'Meteor-Karachi', 'id': 17900002
                }, 'created': 1438040123000, 'rsvp_id': 1562651661, 'mtime': 1438040194000, 'event': {
                    'event_url': 'http://www.meetup.com/Meteor-Karachi/events/223588917/', 'time': 1440252000000, 'name': 'Welcome to Karachi - Meteor', 'id': '223588917'
                }, 'member': {
                    'name': 'kamran', 'member_id': 190405794
                }, 'guests': 1, 'member_photo': {
                    'thumb_link': 'http://photos3.meetupstatic.com/photos/member/c/b/1/0/thumb_248211984.jpeg', 'photo_id': 248211984, 'highres_link': 'http://photos3.meetupstatic.com/photos/member/c/b/1/0/highres_248211984.jpeg', 'photo_link': 'http://photos3.meetupstatic.com/photos/member/c/b/1/0/member_248211984.jpeg'
                }, 'response': 'yes'
        }
        So we will get the member data and issue a member call to get more info
        about member so we can later save him as a candidate
        :param rsvp:
        :return:
        """
        self.traceback_info.update({"functionName": "get_attendee()"})
        events_url = self.api_url + '/member/' \
                     + str(rsvp['member']['member_id']) \
                     + '?sign=true'
        response = self.http_get(events_url)
        if response.ok:
            try:
                data = response.json()
                attendee = Attendee()
                attendee.first_name = data['name'].split(" ")[0]
                if len(data['name'].split(" ")) > 1:
                    attendee.last_name = data['name'].split(" ")[1]
                else:
                    attendee.last_name = ' '
                attendee.full_name = data['name']
                attendee.city = data['city']
                attendee.email = ''
                attendee.country = data['country']
                attendee.profile_url = data['link']
                # attendee.picture_url = data['photo']['photo_link']
                attendee.gt_user_id = self.gt_user_id
                attendee.social_network_id = self.social_network_id
                attendee.rsvp_status = rsvp['response']
                attendee.vendor_rsvp_id = rsvp['rsvp_id']
                attendee.vendor_img_link = "<img class='pull-right' " \
                                           "style='width:60px;height:30px'" \
                                           " src='/web/static/images" \
                                           "/activities/meetup_logo.png'/>"
                # get event from database
                vendor_event_id = rsvp['event']['id']
                epoch_time = rsvp['created']
                dt = milliseconds_since_epoch_to_dt(epoch_time)
                attendee.added_time = dt
                assert vendor_event_id is not None
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.gt_user_id, self.social_network_id, vendor_event_id)
                assert event is not None
                attendee.event = event
                return attendee
            except Exception as e:
                log_exception(self.traceback_info, e.message)
                return None