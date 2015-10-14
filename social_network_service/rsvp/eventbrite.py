"""
This modules contains Eventbrite class. It inherits from RSVPBase class.
Eventbrite contains methods like get_rsvps(), get_attendee() etc.
"""

# Standard Library
import re
from datetime import datetime
from base import RSVPBase

# Application Specific
from common.models.event import Event
from common.models.user import UserSocialNetworkCredential
from common.models.social_network import SocialNetwork
from social_network_service import logger
from social_network_service.utilities import Attendee
from social_network_service.utilities import http_request
from social_network_service.custom_exections import NoUserFound
from social_network_service.custom_exections import EventNotFound


class Eventbrite(RSVPBase):
    """
    - This class is inherited from RSVPBase class.
        RSVPBase class is defined inside social_network_service/rsvp/base.py

    - This implements the following abstract methods

        1- get_rsvps() and
        2- get_attendee() defined in interface.

    - This overrides the process_rsvp() method of base class to raise an
        exception that RSVPs for eventbrite are not imported via manager,
        rather they are imported via webhook.

    - It also defines method process_rsvp_via_webhook() to process the rsvp of
        an event (present on Eventbrite website) using webhook.

    :Example:

        To process rsvp of an eventbrite event (via webhook) you have to do
        following steps:

        1- Import this class
            from social_network_service.rsvp.eventbrite import Eventbrite
                                                            as EventbriteRsvp

        2. First get the user_credentials using webhook_id
            user_credentials =
            EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)

        3. Get the social network class for auth purpose
            user_id = user_credentials.user_id
        social_network_class = get_class(
                    user_credentials.social_network.name.lower(),
                   'social_network')
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token
        sn = social_network_class(
                        user_id=user_credentials.userId,
                        social_network_id=user_credentials.social_network.id)

        4. Get the Eventbrite rsvp class imported and creates rsvp object
            rsvp_class = get_class(
                            user_credentials.social_network.name.lower(),
                            'rsvp')
            rsvp_obj = rsvp_class(user_credentials=user_credentials,
                                  social_network=user_credentials.social_network,
                                  headers=sn.headers)

        5. Call method process_rsvp_via_webhook on rsvp object to process RSVP
            rsvp_obj.process_rsvp_via_webhook(social_network_rsvp_id)

        **See Also**
            .. seealso:: handle_rsvp() function in social_network_service/app/app.py
                         for more insight.

        .. note::
            You can learn more about webhook and eventbrite API from following link
            - https://www.eventbrite.com/developer/v3/
        """

    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)

    @classmethod
    def get_user_credentials_by_webhook(cls, webhook_id):
        """
        :param webhook_id: id of webhook extracted from received data
                        of an rsvp.

        - user credentials db table have a field webhook_id. we pass
            webhook_id in this method and this gives the user's
            (owner of the event for which we are processing rsvp) data.

        - This is a class method which is called from handle_rsvp() function in
            social_network_service/app/app.py

        - We have made this a @classmethod as initially we do not have any
            user credentials to proceed. So we first get the user credentials
            by calling this method on class itself as given in following
            example.

        :Example:

            from social_network_service.rsvp.eventbrite import Eventbrite
            user_credentials = Eventbrite.get_user_credentials_by_webhook(webhook_id)

        **See Also**
            .. seealso:: handle_rsvp() function in social_network_service/app/app.py
                         for more understanding.
        """
        webhook_id_dict = {'webhook_id': webhook_id}
        if webhook_id:
            # gets gt-user object
            social_network = SocialNetwork.get_by_name(cls.__name__)
            user_credentials = UserSocialNetworkCredential.get_by_webhook_id_and_social_network_id(
                webhook_id, social_network.id)
        else:
            raise NoUserFound('Webhook is "%(webhook_id)s"' % webhook_id_dict)
        if user_credentials:
            return user_credentials
        else:
            raise NoUserFound("No User found in database that corresponds to "
                              "webhook id %(webhook_id)s" % webhook_id_dict)

    def process_rsvp_via_webhook(self, rsvp_data):
        """
        :param rsvp_data: is a dict we get from the response of RSVP via
                        webhook

        - This method does the processing to save rsvp in db.

        - This  method is called from process_events_rsvps() function in
            social_network_service/event/eventbrite.py

        :Example:

            - rsvp_obj = rsvp_class(user_credentials=user_credentials,
                                      social_network=user_credentials.social_network,
                                      headers=sn.headers)
            # calls class method to process RSVP
            - rsvp_obj.process_rsvp_via_webhook(social_network_rsvp_id)

        **See Also**
            .. seealso:: process_events_rsvps() function in
                social_network_service/event/eventbrite.py for more understanding.
        """
        if rsvp_data:
            url_of_rsvp = rsvp_data['api_url']
            # gets dictionary object of social_network_rsvp_id
            social_network_rsvp_id = self.get_rsvp_id(url_of_rsvp)
            attendee = self.post_process_rsvp(social_network_rsvp_id)
            if attendee:
                logger.debug('\nRSVP for event "%s" of %s(UserId: %s) has been '
                             'processed and saved successfully in database. '
                             '\nCandidate name is %s.'
                             % (attendee.event.title, self.user.name,
                                self.user.id, attendee.full_name))
            else:
                logger.debug('RSVP(social_network_rsvp_id:%s) of %s(UserId: %s)'
                             ' failed to process.'
                             % (social_network_rsvp_id['rsvp_id'], self.user.name,
                                self.user.id))
        else:
            self.process_rsvps(rsvp_data)

    @staticmethod
    def get_rsvp_id(url):
        """
        This gets the social_network_rsvp_id by comparing url of response of rsvp
        and defined regular expression
        :return:
        """
        regex_to_get_rsvp_id = \
            '^https:\/\/www.eventbriteapi.com\/v3\/orders\/(?P<rsvp_id>[0-9]+)'
        match = re.match(regex_to_get_rsvp_id, url)
        vendor_rsvp_id = match.groupdict()['rsvp_id']
        rsvp = {'rsvp_id': vendor_rsvp_id}
        return rsvp

    def process_rsvps(self, events):
        """
        - As we do not import RSVPs for eventbrite via rsvp importer rather we
          do this via webhook. So, log error if someone tries to run rsvp
          importer for eventbrite.

        - This overrides the base class method process_rsvps().
        """
        raise NotImplementedError("RSVPs for social network %s are handled via"
                                  " webhook. User Id: %s"
                                  % (self.social_network.name, self.user.id))

    def get_rsvps(self, event):
        pass

    def get_attendee(self, rsvp):
        """
        :param rsvp: rsvp is likely the dict we get from the response
            of social network API.

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

        :return: attendee object which contains data about the candidate
        """
        url = self.api_url + "/orders/" + rsvp['rsvp_id']
        response = http_request('GET', url, headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            try:
                data = response.json()
                created_datetime = datetime.strptime(data['created'][:19],
                                                     "%Y-%m-%dT%H:%M:%S")
                attendee = Attendee()
                attendee.first_name = data['first_name']
                attendee.full_name = data['name']
                attendee.last_name = data['last_name']
                attendee.added_time = created_datetime
                attendee.rsvp_status = 'yes' \
                    if data['status'] == 'placed' else data['status']
                attendee.email = data['email']
                attendee.vendor_rsvp_id = rsvp['rsvp_id']
                attendee.gt_user_id = self.user.id
                attendee.social_network_id = self.social_network.id
                attendee.vendor_img_link = \
                    "<img class='pull-right'" \
                    " style='width:60px;height:30px' " \
                    "src='/web/static/images/activities/eventbrite_logo.png'/>"
                # get event_id
                social_network_event_id = data['event_id']
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.user.id, self.social_network.id, social_network_event_id)
                if event:
                    attendee.event = event
                    return attendee
                else:
                    raise EventNotFound('Event is not present in db, '
                                        'social_network_event_id is %s. User Id: %s'
                                        % (social_network_event_id, self.user.id))
            except:
                raise
