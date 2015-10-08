"""
This modules contains Eventbrite class. It inherits from RSVPBase class.
Eventbrite contains methods like get_rsvps(), get_attendee() etc.
"""
from datetime import datetime

from base import RSVPBase
from common.models.event import Event
from common.models.user import UserCredentials
from common.models.social_network import SocialNetwork

from social_network_service import logger
from social_network_service.custom_exections import NoUserFound
from social_network_service.utilities import http_request, Attendee, \
    log_exception, log_error


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

    - It also defines method process_rsvp_via_webhook() to process the rsvp of an
        event (present on Eventbrite website) using webhook.

    :Example:

        To process rsvp of an eventbrite event (via webhook) you have to do
        following steps:

        1- Import this class
            from social_network_service.rsvp.eventbrite import Eventbrite
                                                            as EventbriteRsvp

        2. First get the user_credentials using webhook_id
            user_credentials = EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)

        3. Get the social network class for auth purpose
            user_id = user_credentials.user_id
            social_network_class = get_class(user_credentials.social_network.name.lower(),
                                             'social_network')
            # we call social network class here for auth purpose, If token is expired
            # access token is refreshed and we use fresh token
            sn = social_network_class(user_id=user_credentials.userId,
                                      social_network_id=user_credentials.social_network.id)

        4. Get the Eventbrite rsvp class imported and creates rsvp object
            rsvp_class = get_class(user_credentials.social_network.name.lower(), 'rsvp')
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
    def get_user_credentials_by_webhook(cls, webhook_id, social_network_rsvp_id):
        """
        :param webhook_id: id of webhook extracted from received data
                        of an rsvp.
        :param social_network_rsvp_id: id of rsvp on social network website.

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
        rsvp_data = {'webhook_id': webhook_id,
                     'social_network_rsvp_id': social_network_rsvp_id}
        if webhook_id:
            # gets gt-user object
            social_network = SocialNetwork.get_by_name(cls.__name__)
            user = UserCredentials.get_by_webhook_id_and_social_network_id(
                webhook_id, social_network.id)
        else:
            error_message = 'Webhook is "%(webhook_id)s" for ' \
                            'rsvp(id=%(social_network_rsvp_id)s)' % rsvp_data
            raise NoUserFound('API Error: %s' % error_message)
        if user:
            return user
        else:
            error_message = "No User found in database that corresponds to " \
                            "webhook id %(webhook_id)s" % rsvp_data
            raise NoUserFound('API Error: %s' % error_message)

    def process_rsvp_via_webhook(self, rsvp):
        """
        :param rsvp: is a dict which contains social_network_rsvp_id

        - This method does the processing to save rsvp in db.

        Here we do the followings
            a)- We move on to getting attendee using the given
                rsvp by get_attendees() call. attendees is a utility object we
                 share in calls that contains pertinent data.
                get_attendee() should be implemented by a child.
            b)- We pick the source product of rsvp (e.g. meetup or eventbrite).
            c)- We store the source of candidate in candidate_source db table.
            d)- Once we have the attendees we call save_attendee_as_candidate()
                which store each attendee as a candidate.
            e)- Finally we save the rsvp in rsvp and candidate_event_rsvp db
                tables.

        - This  method is called from handle_rsvp() function in
            social_network_service/app/app.py

        :Example:

            - rsvp_obj = rsvp_class(user_credentials=user_credentials,
                                      social_network=user_credentials.social_network,
                                      headers=sn.headers)
            # calls class method to process RSVP
            - rsvp_obj.process_rsvp_via_webhook(social_network_rsvp_id)

        **See Also**
            .. seealso:: handle_rsvp() function in social_network_service/app/app.py
                         for more understanding.
        """
        try:
            attendee = self.get_attendee(rsvp)
            if attendee:
                # base class method to pick the source product id for
                # attendee
                # and appends in attendee
                attendee = self.pick_source_product(attendee)
                # base class method to store attendees's source event in
                # candidate_source DB table
                attendee = self.save_attendee_source(attendee)
                # base class method to save attendee as candidate in DB
                # table candidate
                attendee = self.save_attendee_as_candidate(attendee)
                # base class method to save rsvp data in DB table rsvp
                attendee = self.save_rsvp(attendee)
                # base class method to save entry in candidate_event_rsvp
                # DB table
                attendee = self.save_candidate_event_rsvp(attendee)
                # base class method to save rsvp data in DB table activity
                self.save_rsvp_in_activity_table(attendee)
            logger.debug('\nRSVP for event "%s" of %s(UserId: %s) has been '
                         'processed and saved successfully in database. '
                         '\nCandidate Name is %s'
                         % (attendee.event.title, self.user.name,
                            self.user.id, attendee.full_name))
        except Exception as e:
            error_message = e.message
            log_exception({'user_id': self.user.id,
                           'error': error_message})
            raise

    def process_rsvps(self, events):
        """
        - As we do not import RSVPs for eventbrite via rsvp importer rather we
          do this via webhook. So, log error if someone tries to run rsvp
          importer for eventbrite.

        - This overrides the base class method process_rsvps().
        """
        log_error({'user_id': self.user.id,
                   'error': NotImplementedError("Eventbrite RSVPs "
                                                "are handled via webhook")})

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
                attendee.rsvp_status = 'yes' if data['status'] == 'placed' else data['status']
                attendee.email = data['email']
                attendee.vendor_rsvp_id = rsvp['rsvp_id']
                attendee.gt_user_id = self.user.id
                attendee.social_network_id = self.social_network.id
                attendee.vendor_img_link = \
                    "<img class='pull-right'" \
                    " style='width:60px;height:30px' " \
                    "src='/web/static/images/activities/eventbrite_logo.png'/>"
                # get event_id
                vendor_event_id = data['event_id']
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.user.id, self.social_network.id, vendor_event_id)
                if event:
                    attendee.event = event
                else:
                    error_message = 'Event is not present in db, VendorEventId is %s' \
                                    % vendor_event_id
                    log_error({'user_id': self.user.id,
                               'error': error_message})
                return attendee
            except Exception as e:
                error_message = e.message
                log_exception({'user_id': self.user.id,
                               'error': error_message})
                raise
