"""
This modules contains Meetup class. It inherits from RSVPBase class.
Meetup contains methods like get_rsvps(), get_attendee() etc.
"""

# Standard Library
from datetime import datetime
from datetime import timedelta

# Application Specific
from base import RSVPBase
from social_network_service.common.models.event import Event
from social_network_service.utilities import Attendee
from social_network_service.utilities import http_request
from social_network_service.custom_exceptions import EventNotFound
from social_network_service.utilities import milliseconds_since_epoch_to_dt


class Meetup(RSVPBase):
    """
    - This class is inherited from RSVPBase class.
    - This implements the following abstract methods

        1- get_rsvps() and
        2- get_attendee() defined in interface.

    :Example:

        - To process rsvp of an Meetup event (via social network manager) you
            have to do following steps:

        1- Create the object of this class by providing required parameters.
            sn_rsvp_obj = Meetup(social_network=self.social_network,
                                headers=self.headers,
                                user_credentials=user_credentials)

        2. Get events of user from db within specified date range
            self.events = self.get_events_from_db(sn_rsvp_obj.start_date_dt)

        3. Get rsvps of all events using API of meetup
            self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)

        4. Call method process_rsvp() on rsvp object to process RSVPs
            sn_rsvp_obj.process_rsvps(self.rsvps)

        **See Also**
            .. seealso:: process_events_rsvps() method in
            social_network_service/event/base.py for more insight.

        .. note::
            You can learn more about Meetup API from following link
            - https://secure.meetup.com/meetup_api/
        """
    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        - Here we set the date range to get events from database.
        """
        super(Meetup, self).__init__(*args, **kwargs)
        self.start_date = kwargs.get('start_date') \
                          or (datetime.now() - timedelta(days=90))
        self.end_date = kwargs.get('end_date') \
                        or (datetime.now() + timedelta(days=90))
        self.start_date_dt = self.start_date
        self.end_date_dt = self.end_date

    def get_rsvps(self, event):
        """
        :param event: event in getTalent database
        :type event: common.models.event.Event
        :return: rsvps of given event
        :rtype: list

        - We get RSVPs of given event by API of Meetup.

        - We use this method while importing RSVPs through social network
            manager.

        :Example:

        - Create RSVP class object as

        sn_rsvp_obj = sn_rsvp_class(social_network=self.social_network,
                                    headers=self.headers,
                                    user_credentials=user_credentials)

        - Then call get_all_rsvps() on sn_rsvp_obj by passing events in
        parameters as follow

            self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)

        - Inside get_all_rsvps(), we call get_rsvps() on class object.

        - It appends rsvps of an events in a list and returns it

        **See Also**
            .. seealso:: get_all_rsvps() method in RSVPBase class
            inside social_network_service/rsvp/base.py for more insight.

        :return: list of rsvps
        """
        rsvps = []
        social_network_id = event.social_network_id
        assert social_network_id is not None
        events_url = self.api_url + '/rsvps/?sign=true&page=100'
        params = {'event_id': event.social_network_event_id}
        response = http_request('GET', events_url, params=params,
                                headers=self.headers,
                                user_id=self.user.id)
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
                response = http_request('GET', next_url + '&sign=true',
                                        user_id=self.user.id)
                if response.ok:
                    data = response.json()
                    rsvps.extend(data['results'])
                    next_url = data['meta']['next'] or None
                    if not next_url:
                        break
            return rsvps

    def get_attendee(self, rsvp):
        """
        :param rsvp: rsvp is likely the response of social network API.
        :type rsvp: dict
        :return: attendee
        :rtype: object

        - This function is used to get the data of candidate related
          to given rsvp. It attaches all the information in attendee object.
          attendees is a utility object we share in calls that contains
          pertinent data.

        - This method is called from process_rsvps() defined in
          RSVPBase class.

        :Example:

            attendee = self.get_attendee(rsvp)

        - RSVP data return from Meetup looks like
            {
            'group': {
                        'group_lat': 24.860000610351562, 'created': 1439953915212,
                        'join_mode': 'open', 'group_lon': 67.01000213623047,
                        'urlname': 'Meteor-Karachi', 'id': 17900002
                    }, 'created': 1438040123000, 'rsvp_id': 1562651661,
            'mtime': 1438040194000,
            'event': {
                        'event_url':
                        'http://www.meetup.com/Meteor-Karachi/events/223588917/',
                        'time': 1440252000000, 'name': 'Welcome to Karachi - Meteor',
                        'id': '223588917'
                    },
            'member': {
                        'name': 'kamran', 'member_id': 190405794
                    },
            'guests': 1, 'member_photo': {
                        'thumb_link':
                        'http://photos3.meetupstatic.com/photos/member/c/b/1/0/
                                                            thumb_248211984.jpeg',
                        'photo_id': 248211984, 'highres_link':
                        'http://photos3.meetupstatic.com/photos/member/c/b/1/0/
                                                            highres_248211984.jpeg',
                        'photo_link':
                        'http://photos3.meetupstatic.com/photos/member/c/b/1/0/
                                                            member_248211984.jpeg'
                    }, 'response': 'yes'
            }
        - So we will get the member data and issue a member call to get more
            info about member so we can later save him as a candidate.

        **See Also**
            .. seealso:: process_rsvps() method in RSVPBase class inside
            social_network_service/rsvp/base.py for more insight.
        """
        events_url = self.api_url + '/member/' \
                     + str(rsvp['member']['member_id']) \
                     + '?sign=true'
        response = http_request('GET', events_url, headers=self.headers,
                                user_id=self.user.id)
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
                attendee.social_profile_url = data['link']
                # attendee.picture_url = data['photo']['photo_link']
                attendee.gt_user_id = self.user.id
                attendee.social_network_id = self.social_network.id
                attendee.rsvp_status = rsvp['response']
                attendee.vendor_rsvp_id = rsvp['rsvp_id']
                attendee.vendor_img_link = "<img class='pull-right' " \
                                           "style='width:60px;height:30px'" \
                                           " src='/web/static/images" \
                                           "/activities/meetup_logo.png'/>"
                # get event from database
                social_network_event_id = rsvp['event']['id']
                epoch_time = rsvp['created']
                dt = milliseconds_since_epoch_to_dt(epoch_time)
                attendee.added_time = dt
                assert social_network_event_id is not None
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.user.id, self.social_network.id,
                    social_network_event_id)
                if event:
                    attendee.event = event
                    return attendee
                else:
                    raise EventNotFound('Event is not present in db, '
                                        'social_network_event_id is %s. '
                                        'User Id: %s'
                                        % (social_network_event_id,
                                           self.user.id))
            except Exception:
                raise
