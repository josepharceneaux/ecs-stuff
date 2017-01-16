"""
This modules contains Meetup class. It inherits from RSVPBase class.
Meetup contains methods like get_rsvps(), get_attendee() etc.
"""

# Standard Library
from datetime import datetime
from datetime import timedelta
import time

# Application Specific
from base import RSVPBase
from social_network_service.modules.urls import get_url
from social_network_service.common.models.event import Event
from social_network_service.custom_exceptions import EventNotFound
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.utilities import Attendee, milliseconds_since_epoch_to_dt
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls as Urls


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
        - Here we set the date range to get events from database.
        """
        super(Meetup, self).__init__(*args, **kwargs)
        self.start_date = kwargs.get('start_date') or (datetime.now() - timedelta(days=90))
        self.end_date = kwargs.get('end_date') or (datetime.now() + timedelta(days=90))
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

        :return: list of RSVPs
        """
        rsvps = []
        social_network_id = event.social_network_id
        assert social_network_id is not None
        rsvps_url = get_url(self, Urls.RSVPS)
        params = {'event_id': event.social_network_event_id}
        response = http_request('GET', rsvps_url, params=params, headers=self.headers, user_id=self.user.id)
        if response.ok:
            data = response.json()
            rsvps.extend(data['results'])
            # next_url determines the pagination, this variable keeps appearing in response if there are more pages
            # and stops showing when there are no more. We have almost the same code for events' pagination,
            # might consolidate it.
            next_url = data['meta']['next'] or None
            while next_url:
                # Sleep for 10 / 30 seconds to avoid throttling
                time.sleep(0.34)
                # attach the key before sending the request
                response = http_request('GET', next_url, headers=self.headers, user_id=self.user.id)
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

        - This method is called from process_rsvps() defined in RSVPBase class.

        :Example:

            attendee = self.get_attendee(rsvp)

        - RSVP data return from Meetup looks like

        In case of RSVPs importer:

        {
            'group': {
                        'group_lat': 24.860000610351562,
                        'created': 1439953915212,
                        'join_mode': 'open',
                        'group_lon': 67.01000213623047,
                        'urlname': 'Meteor-Karachi',
                        'id': 17900002
                    },
            'created': 1438040123000,
            'rsvp_id': 1562651661,
            'mtime': 1438040194000,
            'event': {
                        'name': 'Welcome to Karachi - Meteor',
                        'id': '223588917'
                        'event_url': 'http://www.meetup.com/Meteor-Karachi/events/223588917/',
                        'time': 1440252000000,
                    },
            'member': {
                        'name': 'kamran',
                        'member_id': 190405794
                    },
            'guests': 1,
            'member_photo':
                    {
                        'thumb_link': 'http://photos3.meetupstatic.com/photos/member/c/b/1/0/thumb_248211984.jpeg',
                        'photo_id': 248211984,
                        'highres_link': 'http://photos3.meetupstatic.com/photos/member/c/b/1/0/highres_248211984.jpeg',
                        'photo_link': 'http://photos3.meetupstatic.com/photos/member/c/b/1/0/member_248211984.jpeg'
                    },
            'response': 'yes'
            }

        From streaming API:

        {
            u'group': {
                    u'group_city': u'Denver',
                    u'group_lat': 39.68,
                    u'group_urlname': u'denver-metro-chadd-support',
                    u'group_name': u'Denver-Metro CHADD (Children and Adults with ADHD) Meetup',
                    u'group_lon': -104.92,
                    u'group_topics': [
                                        {u'topic_name': u'ADHD', u'urlkey': u'adhd'},
                                        {u'topic_name': u'ADHD Support', u'urlkey': u'adhd-support'},
                                        {u'topic_name': u'Adults with ADD', u'urlkey': u'adults-with-add'},
                                        {u'topic_name': u'Families of Children who have ADD/ADHD',
                                            u'urlkey': u'families-of-children-who-have-add-adhd'},
                                        {u'topic_name': u'ADHD, ADD', u'urlkey': u'adhd-add'},
                                        {u'topic_name': u'ADHD Parents with ADHD Children',
                                            u'urlkey': u'adhd-parents-with-adhd-children'},
                                        {u'topic_name': u'Resources for ADHD', u'urlkey': u'resources-for-adhd'},
                                        {u'topic_name': u'Parents of Children with ADHD',
                                            u'urlkey': u'parents-of-children-with-adhd'},
                                        {u'topic_name': u'Support Groups for Parents with ADHD Children',
                                            u'urlkey': u'support-groups-for-parents-with-adhd-children'},
                                        {u'topic_name': u'Educators Training on AD/HD',
                                            u'urlkey': u'educators-training-on-ad-hd'},
                                        {u'topic_name': u'Adults with ADHD', u'urlkey': u'adults-with-adhd'}
                                    ],
                    u'group_state': u'CO', u'group_id': 1632579, u'group_country': u'us'
                },
        u'rsvp_id': 1639776896,
        u'venue': {u'lat': 39.674759, u'venue_id': 3407262, u'lon': -104.936317,
                   u'venue_name': u'Denver Academy-Richardson Hall'},
        u'visibility': u'public',
        u'event': {
                        u'event_name': u'Manage the Impact of Technology on Your Child and Family with Lana Gollyhorn',
                        u'event_id': u'235574682',
                        u'event_url': u'https://www.meetup.com/denver-metro-chadd-support/events/235574682/',
                        u'time': 1479778200000
                   },
        u'member': {
                    u'member_name': u'Valerie Brown',
                    u'member_id': 195674019
                    },
        u'guests': 0,
        u'mtime': 1479312043215,
        u'response': u'yes'
        }


        In both cases, we get info of attendee from Meetup API and response looks like

        {
            u'status': u'active',
            u'city': u'Horsham',
            u'name': u'Katalin Nimmerfroh',
            u'other_services': {},
            u'country': u'gb',
            u'topics': [
                        {u'name': u'Musicians', u'urlkey': u'musicians', u'id': 173},
                        {u'name': u'Acting', u'urlkey': u'acting', u'id': 226}
                    ],
            u'lon': -0.33,
            u'joined': 1456995423000,
            u'id': 200820968,
            u'state': u'P6',
            u'link': u'http://www.meetup.com/members/200820968',
            u'photo': {
                    u'thumb_link': u'http://photos2.meetupstatic.com/photos/member/4/f/f/9/thumb_254420473.jpeg',
                    u'photo_id': 254420473,
                    u'highres_link': u'http://photos2.meetupstatic.com/photos/member/4/f/f/9/highres_254420473.jpeg',
                    u'base_url': u'http://photos2.meetupstatic.com',
                    u'type': u'member',
                    u'photo_link': u'http://photos4.meetupstatic.com/photos/member/4/f/f/9/member_254420473.jpeg'
                    },
            u'lat': 51.07,
            u'visited': 1472805623000,
            u'self': {u'common': {}}}


        - So we will get the member data and issue a member call to get more info about member so we can later save
            him as a candidate.

        **See Also**
            .. seealso:: process_rsvps() method in RSVPBase class inside social_network_service/rsvp/base.py
            for more insight.
        """
        if self.rsvp_via_importer:
            social_network_event_id = rsvp['event']['id']
        else:
            social_network_event_id = rsvp['event']['event_id']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(self.user.id, self.social_network.id,
                                                                       social_network_event_id)
        if not event:
            raise EventNotFound('Event is not present in db, social_network_event_id is %s. '
                                'User Id: %s' % (social_network_event_id, self.user.id))

        member_url = self.api_url + '/member/' + str(rsvp['member']['member_id'])
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('GET', member_url, headers=self.headers, user_id=self.user.id)
        if response.ok:
            data = response.json()
            attendee = Attendee()
            attendee.first_name = data['name'].split(" ")[0]
            if len(data['name'].split(" ")) > 1:
                attendee.last_name = data['name'].split(" ")[1]
            else:
                attendee.last_name = ' '
            attendee.full_name = data['name']
            attendee.city = data['city']
            attendee.email = ''  # Meetup API does not expose this
            attendee.country = data['country']
            attendee.social_profile_url = data['link']
            # attendee.picture_url = data['photo']['photo_link']
            attendee.gt_user_id = self.user.id
            attendee.social_network_id = self.social_network.id
            attendee.rsvp_status = rsvp['response']
            attendee.vendor_rsvp_id = rsvp['rsvp_id']
            # TODO: This won't work now, need to figure out a way
            attendee.vendor_img_link = "<img class='pull-right' " \
                                       "style='width:60px;height:30px'" \
                                       " src='/web/static/images" \
                                       "/activities/meetup_logo.png'/>"
            # get event from database
            epoch_time = rsvp['mtime']
            dt = milliseconds_since_epoch_to_dt(epoch_time)
            attendee.added_time = dt
            attendee.event = event
            return attendee
