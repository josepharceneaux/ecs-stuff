"""
This is a base class which all importers (meetup, eventbrite and etc)
will inherit. Derived classes would usually implement the following:
get_all_user_credentials()
get_events()
normalize_event()
get_rsvps()
and get_attendee().
"""
import logging
import json
import requests
from event_importer.utilities import log_error, log_exception
from gt_models.product import Product
from gt_models.social_network import SocialNetwork
from gt_models.user import UserCredentials
from gt_models.event import Event
from gt_models.rsvp import RSVP, CandidateEventRSVP
from gt_models.candidate import Candidate, CandidateSource
from gt_models.config import init_db
from gt_models.activity import Activity

logger = logging.getLogger('event_service.app')


class Base(object):
    def __init__(self, *args, **kwargs):
        self.start_date = None
        self.end_date = None
        self.start_date_dt = None
        self.events = []
        self.attendees = []
        self.all_user_credentials = []
        self.vendor = None
        self.user_credential = None
        self.api_url = None
        self.access_token = None
        self.member_id = None
        self.headers = None
        self.traceback_info = None
        self.gt_user_id = None
        self.social_network_id = None
        self.alchemy_session_init = kwargs.get('alchemy_session_init') or None
        if not self.alchemy_session_init:
            init_db()

    def token_validity(self, access_token):
        """
        This checks the validity of access_token.
        Child classes will implement this according to its respective API
        to check if token is valid or expired.
        :param access_token:
        :return:
        """
        return True

    def refresh_token(self):
        """
        This function refreshes the token if expired.
        Child class will implement this according to its respective API
        :return:
        """
        pass

    def set_user_credential(self, user_credential_obj):
        """
        sets user's credentials as base class object so that it is
        available in child classes.It also sets the traceback_info as base
        class object to be used in logging purpose.
        traceback_info is used while logging an exception or error.
        traceback_info contains User's Name, MemberId of user on vendor,
        Function name where exception occurs,Class Name of calling object
        and Error message to be logged.
        In every function where exception is thrown, functionName is appended
        in the traceback_info.
        If user credentials are not "None", we set api_url, access_token,
        member_id, gt_user_id, social_network_id and traceback_info as base
        class objects so any child class can use them. If any of them is
        missing, we log an error with missing items.
        (api_url is not checked as for Facebook we don't have any api url)
        :param user_credential_obj:
        :return:
        """
        self.user_credential = user_credential_obj
        if self.user_credential:
            self.traceback_info = {
                'User': self.user_credential.user.firstName
                        + ' ' + self.user_credential.user.lastName,
                'memberId': self.user_credential.memberId,
                'class': self.vendor,
                'functionName': 'set_user_credential()',
                'error': ''}
            data = {
                "access_token": self.user_credential.accessToken,
                "member_id": self.user_credential.memberId,
                "gt_user_id": self.user_credential.userId,
                "social_network_id": self.user_credential.social_network.id,
                "api_url": self.user_credential.social_network.apiUrl
            }
            # checks if any field is missing for given user credentials
            items = [value for key, value in data.iteritems() if key is not "api_url"]
            if all(items):
                self.api_url = data['api_url']
                self.member_id = data['member_id']
                self.gt_user_id = data['gt_user_id']
                self.social_network_id = data['social_network_id']
                # token validity is checked here
                # if token is expired, we refresh it here
                if not self.token_validity(data['access_token']):
                    # token is expired, get fresh token from vendor
                    self.access_token = self.refresh_token()
                else:
                    # token is valid, so proceed normally
                    self.access_token = data['access_token']
                self.headers = {'Authorization': 'Bearer ' + self.access_token}
            else:
                # gets fields which are missing
                items = [key for key, value in data.iteritems()
                         if key is not "api_url" and not value]
                missing_items = dict(missing_items=items)
                # Log those fields in error which are not present in Database
                log_error(self.traceback_info,
                          "Missing Item(s) in user's credential: "
                          "%(missing_items)s\n" % missing_items)
        else:
            logger.error("User credentials are None")

    def get_all_user_credentials(self):
        """
        We get all user credentials that belongs to a particular social network.
        :return:
        """
        social_network = SocialNetwork.get_by_name(self.vendor)
        self.all_user_credentials = UserCredentials.get_user_credentials_of_social_network(
            social_network.id
        )

    def get_user_credentials(self, user_id=None):
        """
        We get all user credentials that belongs to a particular social network.
        Inherited class should implement this.
        :return:
        """
        assert self.vendor is not None
        social_network = SocialNetwork.get_by_name(self.vendor)
        self.all_user_credentials = UserCredentials.get_user_credentials_of_social_network(
            social_network.id
        )
        if user_id:
            self.all_user_credentials = filter(lambda user_creds: user_creds.userId == user_id,
                                               self.all_user_credentials)

    def http_get(self, url, params=None, data=None):
        """
        This code is used to make GET call on given url and handles exceptions
        """
        headers = self.headers
        try:
            response = requests.get(url, params, headers=headers)
            # If we made a bad request (a 4XX client error or 5XX server error response),
            # we can raise it with Response.raise_for_status():"""
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log_exception(self.traceback_info, e.message)
        except requests.RequestException as e:
            log_exception(self.traceback_info, e.message)
        return response

    def get_events(self):
        """
        This will get events from Vendor's servers and all
        events will be stored in self.events, where each event
        will be contained in a dict.
        Inherited class will do the implementation for this.
        :return:
        """
        pass

    def get_event(self, id):
        pass

    def create_event(self, *args, **kwargs):
        """
        Inherited class will do the implementation.
        :return:
        """
        pass

    def normalize_event(self, event):
        """
        We will basically take the vendor's event data and map it to
        getTalent's event format. That is, we return event which is
        a type of Event (defined under gt_models/event.py).
        So inherited class will do the implementation.
        :param event:
        :return:
        """
        pass

    def _process_events(self):
        events = self.get_events()
        self.pre_process_events(events)
        for event in events:
            event = self.normalize_event(event)
            if event:
                event_in_db = Event.get_by_user_and_vendor_id(event.userId,
                                                              event.vendorEventId)
                if event_in_db:
                    data = dict(eventTitle=event.eventTitle,
                                eventDescription=event.eventDescription,
                                eventAddressLine1=event.eventAddressLine1,
                                eventStartDateTime=event.eventStartDateTime,
                                eventEndDateTime=event.eventEndDateTime)
                    event_in_db.update(**data)
                else:
                    Event.save(event)
        self.post_process_events()

    def pre_process_events(self, events):
        """
        Can be used in future for any pre processing.
        Child class will contain the implementation.
        :return:
        """
        pass

    def post_process_events(self):
        """
        Can be used in future for any post processing.
        Child class will contain the implementation.
        :return:
        """
        pass

    def get_rsvps(self, event):
        pass

    def _process_rsvps(self):
        """
        We get events against a particular user_credential and then we go over
        each event one by one and do the following:
            a)- Get RSVPs of that event. This is done in the get_rsvps()
            method which gets RSVPs and attach them to rsvps list of dicts.
            This method get_rsvps() should be implemented by a child as
            implementation may vary across vendors.
            b)- Then we store all RSVPs (given in the rsvps). This
            is done in save_rsvps()
            c)- Then we move on to getting attendees using the given
            RSVPs (and those are in rsvps). get_attendees() call
            get_attendee() which should be implemented by a child.
            d)- Once we have the list of attendees we call
            save_attendees_as_candidate() which take attendees (as
            given in self.attendees) and store each attendee as
            a candidate.
        :return:
        """
        self.traceback_info.update({"function_name": "_process_events()"})
        # get events from database where eventStartDate is greater than
        # self.start_date
        events = Event.get_by_user_id_vendor_id_start_date(self.gt_user_id,
                                                           self.social_network_id,
                                                           self.start_date_dt,
                                                           )
        if events:
            for event in events:
                # events is a list of dicts. where each dict is likely a
                # response return from the database
                # we pick one event from events_list, start doing rsvp
                # processing.
                # rsvps is a list of dicts, where each dict is likely a response
                # return from the vendor's side.
                try:
                    rsvps = self.get_rsvps(event)
                except Exception as e:
                    event['error_message'] = e.message
                    # Shouldn't raise an exception, just log it and move to process
                    # process next RSVP
                    log_exception(self.traceback_info,
                                  "Couldn't get RSVPs for "
                                  "eventName: %(eventTitle)s, "
                                  "eventId on Vendor: %(vendorEventId)s,"
                                  "error message: %(error_message)s"
                                  % event)
                else:
                    if rsvps:
                        # attendees is a utility object we share in calls that
                        # contains pertinent data
                        attendees = self.get_attendees(rsvps)
                        # following picks the source product id for attendee
                        attendees = self.pick_source_products(attendees)
                        # following will store candidate info in attendees
                        attendees = self.save_attendees_source(attendees)
                        # following will store candidate info in attendees
                        attendees = self.save_attendees_as_candidates(attendees)
                        # following call will store rsvp info in attendees
                        attendees = self.save_rsvps(attendees)
                        # finally we store info in candidate_event_rsvp table for
                        # attendee
                        attendees = self.save_candidates_events_rsvps(attendees)
                        self.save_rsvps_in_activity_table(attendees)
                    elif rsvps is None:
                        break
        else:
            log_error(self.traceback_info,
                      "There are no events for User in the Database")

    def get_attendees(self, rsvps):
        """
        This calls get_attendee() which is usually implemented by the child
        because implementation may vary across different vendors.
        :param rsvps:
        :return:
        """
        self.attendees = map(self.get_attendee, rsvps)
        # only picks those attendees for which we are able to get data
        # rest attendees are logged and are not processed further
        self.attendees = filter(lambda attendee: attendee is not None,
                                self.attendees)
        return self.attendees

    def get_attendee(self, rsvp):
        pass

    def pick_source_products(self, attendees):
        return map(self.pick_source_product, attendees)

    def pick_source_product(self, attendee):
        """
        Here we pick the id of source product by providing vendor name
        and appends it attendee object
        :param attendee:
        :return:attendee
        """
        source_product = Product.get_by_name(self.vendor)
        attendee.source_product_id = source_product.id
        return attendee

    def save_attendees_source(self, attendees):
        return map(self.save_attendee_source, attendees)

    def save_attendee_source(self, attendee):
        """
        Checks if the event is present in candidate_source DB table.
        If does not exist, adds record. Appends id of source in
        attendee object to be saved in candidate table.
        :param attendee:
        :return:attendee
        """
        entry_in_db = CandidateSource.get_by_description_and_notes(
            attendee.event.eventTitle,
            attendee.event.eventDescription)
        data = {'description': attendee.event.eventTitle,
                'notes': attendee.event.eventDescription[:495],  # field is 500 chars
                'domainId': 1}
        if entry_in_db:
            entry_in_db.update(**data)
            entry_id = entry_in_db.id
        else:
            entry = CandidateSource(**data)
            CandidateSource.save(entry)
            entry_id = entry.id
        attendee.candidate_source_id = entry_id
        return attendee

    def save_attendees_as_candidates(self, attendees):
        return map(self.save_attendee_as_candidate, attendees)

    def save_attendee_as_candidate(self, attendee):
        """
        Add the attendee as a new candidate if it is not present in the
        database already and also add the candidate_id to the attendee object
        and return attendee object.
        :param attendee:
        :return:
        """
        newly_added_candidate = 1  # 1 represents entity is new candidate
        candidate_in_db = \
            Candidate.get_by_first_last_name_owner_user_id_source_id_product(
                attendee.first_name,
                attendee.last_name,
                attendee.gt_user_id,
                attendee.candidate_source_id,
                attendee.source_product_id)
        data = {'firstName': attendee.first_name,
                'lastName': attendee.last_name,
                'addedTime': attendee.added_time,
                'ownerUserId': attendee.gt_user_id,
                'statusId': newly_added_candidate,
                'sourceId': attendee.candidate_source_id,
                'sourceProductId': attendee.source_product_id}
        if candidate_in_db:
            candidate_in_db.update(**data)
            candidate_id = candidate_in_db.id
        else:
            candidate = Candidate(**data)
            Candidate.save(candidate)
            candidate_id = candidate.id
        attendee.candidate_id = candidate_id
        return attendee

    def save_rsvps(self, attendees):
        return map(self.save_rsvp, attendees)

    def save_rsvp(self, attendee):
        """
        Add a new RSVP object if it is not present in the db already
        and add the id to attendee object and return attendee object as well.
        :param attendee:
        :return: attendee
        """
        rsvp_in_db = RSVP.get_by_vendor_rsvp_id_candidate_id_vendor_id_event_id(
            attendee.vendor_rsvp_id,
            attendee.candidate_id,
            attendee.social_network_id,
            attendee.event.id)
        data = {
            'candidateId': attendee.candidate_id,
            'eventId': attendee.event.id,
            'socialNetworkId': attendee.social_network_id,
            'rsvpStatus': attendee.rsvp_status,
            'vendorRsvpId': attendee.vendor_rsvp_id,
            'rsvpDateTime': attendee.added_time
        }
        if rsvp_in_db:
            rsvp_in_db.update(**data)
            rsvp_id_db = rsvp_in_db.id
        else:
            rsvp = RSVP(**data)
            RSVP.save(rsvp)
            rsvp_id_db = rsvp.id
        attendee.rsvp_id = rsvp_id_db
        return attendee

    def save_candidates_events_rsvps(self, attendees):
        return map(self.save_candidate_event_rsvp, attendees)

    def save_candidate_event_rsvp(self, attendee):
        """
        Add an entry for every rsvp in candidate_event_rsvp table if
        entry is not present already using candidate_id, event_id and
        rsvp_id. It appends id of entry in table in attendee object and
        returns attendee object
        :param attendee:
        :return: attendee
        """
        entity_in_db = CandidateEventRSVP.get_by_id_of_candidate_event_rsvp(
            attendee.candidate_id,
            attendee.event.id,
            attendee.rsvp_id)
        data = {'candidateId': attendee.candidate_id,
                'eventId': attendee.event.id,
                'rsvpId': attendee.rsvp_id}
        if entity_in_db:
            entity_in_db.update(**data)
            entity_id = entity_in_db.id
        else:
            candidate_event_rsvp = CandidateEventRSVP(**data)
            CandidateEventRSVP.save(candidate_event_rsvp)
            entity_id = candidate_event_rsvp.id
        attendee.candidate_event_rsvp_id = entity_id
        return attendee

    def save_rsvps_in_activity_table(self, attendees):
        self.attendees = map(self.save_rsvp_in_activity_table, attendees)
        return self.attendees

    def save_rsvp_in_activity_table(self, attendee):
        """
        Once rsvp is stored in all required tables, here we update Activity table
        so that Get Talent user can see rsvps in Activity Feed
        :param attendee:
        :return:
        """
        assert attendee.event.eventTitle is not None
        event_title = attendee.event.eventTitle
        gt_user_first_name = self.user_credential.user.firstName
        gt_user_last_name = self.user_credential.user.lastName
        type_of_rsvp = 23  # to show message on activity feed
        first_name = attendee.first_name
        last_name = attendee.last_name
        params = {'firstName': first_name,
                  'lastName': last_name,
                  'eventTitle': event_title,
                  'response': attendee.rsvp_status,
                  'img': attendee.vendor_img_link,
                  'creator': '%s' % gt_user_first_name + ' %s' % gt_user_last_name}
        activity_in_db = Activity.get_by_user_id_params_type_source_id(
            attendee.gt_user_id,
            json.dumps(params),
            type_of_rsvp,
            attendee.candidate_event_rsvp_id)
        data = {'sourceTable': 'candidate_event_rsvp',
                'sourceId': attendee.candidate_event_rsvp_id,
                'addedTime': attendee.added_time,
                'type': type_of_rsvp,
                'userId': attendee.gt_user_id,
                'params': json.dumps(params)}
        if activity_in_db:
            activity_in_db.update(**data)
        else:
            candidate_activity = Activity(**data)
            Activity.save(candidate_activity)
        return attendee
