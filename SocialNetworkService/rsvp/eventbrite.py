from base import RSVPBase
from datetime import datetime, timedelta
from common.gt_models.event import Event
from SocialNetworkService.utilities import http_request, Attendee, \
    log_exception, log_error, get_message_to_log
from common.gt_models.user import UserCredentials


class EventbriteRsvp(RSVPBase):
    """
    Here we implement the code related to RSVPs of meetup event
    """
    def __init__(self, *args, **kwargs):
        super(EventbriteRsvp, self).__init__(*args, **kwargs)
        function_name = '__init__()'
        self.message_to_log.update({'function_name': function_name,
                                    'class_name': self.__class__.__name__,
                                    'fileName': __file__})
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
                                            class_name=cls.__class__.__name__)
        if webhook_id:
            try:
                # gets gt-user object
                user = UserCredentials.get_by_webhook_id(webhook_id)
                webhook = {'webhook_id': webhook_id}
            except Exception as e:
                error_message = e.message
                message_to_log.update({'error': error_message})
                log_exception(message_to_log)
        else:
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
        self.message_to_log.update({'functionName': '_process_rsvp_via_webhook()'})
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
            self.message_to_log.update({'error': error_message})
            log_exception(self.message_to_log)

    def _process_rsvps(self):
        self.message_to_log.update({'functionName': '_process_rsvps()',
                                    'error': NotImplementedError("Eventbrite RSVPs are "
                                                                 "handled via webhook")})
        log_exception(self.message_to_log)
        raise

    def get_rsvps(self, event):
        pass

    def get_attendee(self, rsvp):
        """
        Here Data about attendee is gathered by api_call to the vendor
        :param rsvp: contains the id of rsvp for (eventbrite) in dictionary format
        :return: attendee object which contains data of the attendee
        """
        self.message_to_log.update({"functionName": "get_attendee()"})
        attendee = None
        url = self.api_url + "/orders/" + rsvp['rsvp_id']
        response = http_request('GET', url, headers=self.headers,
                                message_to_log=self.message_to_log)
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
                attendee.gt_user_id = self.gt_user_id
                attendee.social_network_id = self.social_network_id
                attendee.vendor_img_link = \
                    "<img class='pull-right'" \
                    " style='width:60px;height:30px' " \
                    "src='/web/static/images/activities/eventbrite_logo.png'/>"
                # get event_id
                vendor_event_id = data['event_id']
                event = Event.get_by_user_id_social_network_id_vendor_event_id(
                    self.gt_user_id, self.social_network_id, vendor_event_id)
                if event:
                    attendee.event = event
                else:
                    error_message = 'Event is not present in db, VendorEventId is %s' \
                                    % vendor_event_id
                    self.message_to_log.update({'error': error_message})
                    log_error(self.message_to_log)
            except Exception as e:
                error_message = e.message
                self.message_to_log.update({'error': error_message})
                log_exception(self.message_to_log)
            return attendee
