from base import RSVPBase
from datetime import datetime, timedelta
from common.models.event import Event
from social_network_service.utilities import http_request, Attendee, \
    log_exception, log_error, get_message_to_log
from common.models.user import UserCredentials


class Eventbrite(RSVPBase):
    """
    Here we implement the code related to RSVPs of meetup event
    """
    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)
        self.start_date_in_utc = (datetime.now() -
                                  timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def get_user_credentials_by_webhook(cls, webhook_id):
        """
        This gives the Owner user's data using following class variables
        webhook_id: is the id of webhook of the Get Talent user
        social_network_id: is the id of social network of Get Talent user
        """
        user = None
        webhook = None
        function_name = 'get_user_credentials_by_webhook()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            file_name=__file__,
                                            class_name=cls.__class__.__name__,)
        if webhook_id:
            try:
                # gets gt-user object
                user = UserCredentials.get_by_webhook_id(webhook_id)
                webhook = {'webhook_id': webhook_id}
            except Exception as e:
                error_message = e.message
                message_to_log.update({'error': error_message})
                log_exception(message_to_log)
                # raise the error TODO
        else:
            # TODO may be following is redudant, we should just assert on
            # webhook_id at the top and remove this else
            error_message = 'Webhook Id is None. Can not Process RSVP'
            message_to_log.update({'error': error_message})
            log_error(message_to_log)
        if user:
            return user
        else:
            error_message = "No User found in database corresponding to webhook id " \
                            "%(webhook_id)s" % webhook
            message_to_log.update({'error': error_message})
            log_error(message_to_log)

    def _process_rsvp_via_webhook(self, rsvp):
        """
        Here we handle the RSVP of an event through webhook
        :param rsvp:
        :return:
        """
        function_name = '_process_rsvp_via_webhook()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
        # TODO assert on rsvp i.e. chekc it is the correct type
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
        except Exception as e:
            # Shouldn't raise an exception, just log it and move to process
            # process next RSVP
            error_message = e.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
            #TODO should we raise, if so raise it

    def process_rsvps(self, events):
        """
        Here we process the rsvp for rsvp importer
        """
        #TODO double check this paproach and logging will change throughout
        function_name = 'process_rsvps()'
        message_to_log = get_message_to_log(
            function_name=function_name,
            class_name=self.__class__.__name__,
            gt_user=self.user.name,
            file_name=__file__,
            error=NotImplementedError("Eventbrite RSVPs are "
                                      "handled via webhook"))
        log_error(message_to_log)

    def get_rsvps(self, event):
        pass

    def get_attendee(self, rsvp):
        """
        Here Data about attendee is gathered by api_call to the vendor
        :param rsvp: contains the id of rsvp for (eventbrite) in dictionary format
        :return: attendee object which contains data of the attendee
        """
        # TODO assert on rsvp
        function_name = 'get_attendee()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
        attendee = None
        url = self.api_url + "/orders/" + rsvp['rsvp_id']
        response = http_request('GET', url, headers=self.headers,
                                message_to_log=message_to_log)
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
                attendee.social_network_id = self.social_network_id
                attendee.vendor_img_link = \
                    "<img class='pull-right'" \
                    " style='width:60px;height:30px' " \
                    "src='/web/static/images/activities/eventbrite_logo.png'/>"
                # get event_id
                vendor_event_id = data['event_id']
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.user.id, self.social_network_id, vendor_event_id)
                if event:
                    attendee.event = event
                else:
                    error_message = 'Event is not present in db, VendorEventId is %s' \
                                    % vendor_event_id
                    message_to_log.update({'error': error_message})
                    log_error(message_to_log)
            except Exception as e:
                error_message = e.message
                message_to_log.update({'error': error_message})
                log_exception(message_to_log)
                # TODO I think we should raise here.
            return attendee
