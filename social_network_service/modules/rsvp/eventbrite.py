"""
This modules contains Eventbrite class. It inherits from RSVPBase class.
Eventbrite contains methods like get_rsvps(), get_attendee() etc.
"""

# Standard Library
import re
from datetime import datetime
from base import RSVPBase

# Application Specific
#TODO: Added unused import
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.models.event import Event
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.utilities import Attendee
from social_network_service.social_network_app import logger


class Eventbrite(RSVPBase):
    """
    - This class is inherited from RSVPBase class.
        RSVPBase class is defined inside social_network_service/rsvp/base.py

    - This implements the following abstract methods

        1- get_rsvps() and
        2- get_attendee() defined in interface.

    :Example:

        To process rsvp of an eventbrite event you have to do
        following steps:

        1- Import this class
            from social_network_service.rsvp.eventbrite import Eventbrite
                                                            as EventbriteRsvp

        2. Get the social network class for auth purpose
            user_id = user_credentials.user_id
        social_network_class = get_class(
                    user_credentials.social_network.name.lower(),
                   'social_network')
        we call social network class here for auth purpose, If token is
        expired, access token is refreshed and we use fresh token
        sn = social_network_class(
                        user_id=user_credentials.userId,
                        social_network_id=user_credentials.social_network.id)

        3. Get the Eventbrite rsvp class imported and creates rsvp object
            rsvp_class = get_class(
                            user_credentials.social_network.name.lower(),
                            'rsvp')
            rsvp_obj = rsvp_class(
            user_credentials=user_credentials,
            social_network=user_credentials.social_network,headers=sn.headers)

        4. Call get_all_rsvps method to get all Attendees of current user_credentials

        **See Also**
            .. seealso:: handle_rsvp() function in
                social_network_service/app/app.py for more insight.

        .. note::
            You can learn more about webhook and eventbrite API from following
            link - https://www.eventbrite.com/developer/v3/
        """
    # TODO: We can make example of code in docs clearer by >>> symbol

    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)

    # TODO: I think this is no longer needed
    @staticmethod
    def get_rsvp_id(url):
        """
        :param url: url we get from the response of RSVP via webhook
        :type url: str

        This gets the social_network_rsvp_id by comparing url of response of
        rsvp and defined regular expression
        :return: social_network_rsvp_id
        :rtype: dict
        """
        regex_to_get_rsvp_id = \
            '^https:\/\/www.eventbriteapi.com\/v3\/orders\/(?P<rsvp_id>[0-9]+)'
        match = re.match(regex_to_get_rsvp_id, url)
        social_network_rsvp_id = match.groupdict()['rsvp_id']
        rsvp = {'rsvp_id': social_network_rsvp_id}
        return rsvp

    def get_all_rsvps(self, events=None):
        """
        - This method is used to get all attendees from each eventbrite events of a user
        :param events: Eventbrite events object
        :return: list of rsvps
        """
        # TODO: Unused param events
        rsvp_url = self.api_url + '/users/%s/owned_event_attendees'
        response = http_request('GET', headers=self.headers,
                                url=rsvp_url
                                % self.user_credentials.member_id)
        all_rsvps = []
        data = response.json()
        page_size = data['pagination']['page_size']
        total_records = data['pagination']['object_count']

        all_rsvps.extend(data['attendees'])
        current_page = 1
        total_pages = total_records / page_size
        for page in range(1, total_pages):
            params = {'page': current_page}
            current_page += 1
            # get data for every page
            response = http_request('GET', rsvp_url,
                                    params=params,
                                    headers=self.headers,
                                    user_id=self.user_credentials.id)
            if response.ok:
                data = response.json()
                all_rsvps.extend(data['attendees'])

        return all_rsvps

    def get_rsvps(self, event):
        # TODO: Add docs why only pass here
        pass
        # TODO: I think we can retrieve attendees of a single event of Eventbrite.
        # TODO: See this url = self.api_url + "/events/" + str(event.social_network_event_id) + '/attendees/'

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

        - It is also called from process_rsvps_via_webhook() in
          rsvp/eventbrite.py

        :Example:

            attendee = self.get_attendee(rsvp)

        **See Also**
            .. seealso:: process_rsvps() method in RSVPBase class inside
                social_network_service/rsvp/base.py

            .. seealso:: process_rsvps_via_webhook() method in class Eventbrite
                inside social_network_service/rsvp/eventbrite.py
        """
        # TODO: Correct rtype as you did at other places
        # get event_id
        social_network_event_id = rsvp['event_id']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(
            self.user.id, self.social_network.id,
            social_network_event_id)
        if not event:
            # logger.error?
            logger.info('Event is not present in db, '
                        'social_network_event_id is '
                        '%s. User Id: %s'
                        % (social_network_event_id,
                           self.user.id))
            return None

        created_datetime = datetime.strptime(rsvp['created'][:19],
                                             "%Y-%m-%dT%H:%M:%S")
        attendee = Attendee()
        attendee.first_name = rsvp['profile']['first_name']
        attendee.full_name = rsvp['profile']['name']
        attendee.last_name = rsvp['profile']['last_name']
        attendee.added_time = created_datetime
        attendee.rsvp_status = 'yes' \
            if rsvp['status'].lower() == 'placed' else rsvp['status']
        attendee.email = rsvp['profile']['email']
        attendee.vendor_rsvp_id = rsvp['id']
        attendee.gt_user_id = self.user.id
        attendee.social_network_id = self.social_network.id
        attendee.vendor_img_link = \
            "<img class='pull-right'" \
            " style='width:60px;height:30px' " \
            "src='/web/static/images/activities/eventbrite_logo.png'/>"
        attendee.social_profile_url = rsvp['resource_uri']
        attendee.event = event
        # Get profile url of candidate to save
        return attendee
