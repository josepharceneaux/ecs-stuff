import requests

from datetime import datetime, timedelta
from common.models.event import Event
from social_network_service.rsvp.base import RSVPBase
from social_network_service.utilities import Attendee, log_exception, \
    import_from_dist_packages, log_error, get_message_to_log

# Here we import facebook-sdk python module making sure it doesn't import
# our local facebook.py modules
facebook = import_from_dist_packages('facebook')


class Facebook(RSVPBase):
    """
    This class implements all functions required to import
    users' events from facebook and their RSVPs.
    """

    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)
        self.start_date = (datetime.now() - timedelta(days=3000)).strftime("%Y-%m-%d")
        self.end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.start_date_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        self.end_date_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        self.graph = None

    def get_rsvps(self, event):
        """
        This method retrieves RSPVs for user's events on Facebook.
        """
        function_name = "get_rsvps()"
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
        rsvps = []
        try:
            self.graph = facebook.GraphAPI(access_token=self.access_token)
            url = 'v2.4/%s' % str(event.social_network_event_id) + '/'
            # Get list of people surely attending
            confirm_attendees = self.graph.get_object(url + 'attending')
        except facebook.GraphAPIError as error:
            error_message = "Couldn't get 'attending' RSVPs (Facebook). %s" % error.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
            raise
        rsvps += confirm_attendees['data']
        self.get_all_pages(confirm_attendees, rsvps)
        # Get list of people who aren't certain
        try:
            expected_attendees = self.graph.get_object(url + 'maybe')
        except facebook.GraphAPIError as error:
            error_message = "Couldn't get 'maybe' RSVPs (Facebook). %s" % error.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
            raise
        rsvps += expected_attendees['data']
        self.get_all_pages(expected_attendees, rsvps)
        # Get list of people who declined
        try:
            declined_attendees = self.graph.get_object(url + 'declined')
        except facebook.GraphAPIError as error:
            error_message = "Couldn't get 'Declined' RSVPs (Facebook). %s" % error.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
            raise
        rsvps += declined_attendees['data']
        self.get_all_pages(declined_attendees, rsvps)
        for rsvp in rsvps:
            rsvp.update({'vendor_event_id': str(event.social_network_event_id)})
        return rsvps

    def get_all_pages(self, response, target_list):
        function_name = "get_all_pages()"
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
        while True:
            try:
                response = requests.get(response['paging']['next'])
                if response.ok:
                    response = response.json()
                if response and response['data']:
                    target_list.extend(response['data'])
            except KeyError:
                break
            except requests.HTTPError as error:
                error_message_dict = dict(url=response['paging']['next'],
                                          error_message=error.message)
                error_message = "Couldn't get data while paginating over Facebook records. " \
                                "URL: %(url)s, %(error_message)s" % error_message_dict
                message_to_log.update({'error': error_message})
                log_exception(message_to_log)
                raise

    def get_attendee(self, rsvp):
        """
        RSVP data returned from Facebook API looks like
        So we will get the member data and issue a member call to get more info
        about member so we can later save him as a candidate
        :param rsvp:
        :return:
        """
        function_name = "get_attendee()"
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
        try:
            data = self.graph.get_object('v2.4/' + rsvp['id'],
                                         fields='first_name, last_name, name, '
                                                'email, location, address, link, picture')
        except facebook.GraphAPIError as error:
            error_message = "Couldn't get Facebook's attendee info. %s" % error.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
            raise
        if 'location' in data:
            try:
                location = self.graph.get_object('v2.4/'
                                                 + data['location']['id'],
                                                 fields='location')
            except facebook.GraphAPIError as error:
                error_message = " Couldn't get location info (Facebook). %s" % error.message
                message_to_log.update({'error': error_message})
                log_exception(message_to_log)
                raise
            if 'location' in location:
                location = location['location']
        else:
            location = {}
        attendee = None
        if data:
            try:
                attendee = Attendee()
                attendee.first_name = data.get('first_name', '')
                attendee.last_name = data.get('last_name', '')
                attendee.full_name = data.get('name', '')
                attendee.email = data.get('email', '')
                attendee.city = location.get('city', '')
                attendee.country = location.get('country', '')
                attendee.latitude = location.get('latitude')
                attendee.longitude = location.get('longitude')
                attendee.zip = location.get('zip')
                attendee.profile_url = data.get('link', '')
                attendee.picture_url = data['picture']['data']['url'] if 'picture' in data else ''
                attendee.gt_user_id = self.user.id
                attendee.social_network_id = self.social_network_id
                attendee.vendor_rsvp_id = rsvp['id']  # we are using profile_id
                # here as we do not have any rsvp_id for this vendor
                attendee.added_time = ' '
                attendee.vendor_img_link = "<img class='pull-right' " \
                                           "style='width:60px;height:30px' " \
                                           "src='/web/static/images/activities/facebook_logo.png'/>"
                vendor_event_id = rsvp['vendor_event_id']
                if rsvp['rsvp_status'].strip() == 'attending' \
                        or rsvp['rsvp_status'].strip() == 'maybe':
                    attendee.rsvp_status = 'yes'
                else:
                    attendee.rsvp_status = 'no'
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
            return attendee
