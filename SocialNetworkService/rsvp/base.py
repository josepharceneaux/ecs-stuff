import json

from abc import ABCMeta, abstractmethod
from common.gt_models.event import Event
from common.gt_models.product import Product
from common.gt_models.activity import Activity
from common.gt_models.rsvp import RSVP, CandidateEventRSVP
from common.gt_models.candidate import CandidateSource, Candidate
from SocialNetworkService.utilities import log_exception, log_error


class RSVPBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        function_name = '__init__()'

        self.message_to_log = kwargs.get('message_to_log')
        self.message_to_log.update({'function_name': function_name,
                                    'class_name': self.__class__.__name__})
        try:
            self.headers = kwargs.get('headers')
            self.user_credentials = kwargs.get('user_credentials')
            self.gt_user_id = self.user_credentials.userId
            self.social_network_id = kwargs.get('social_network').id
            self.social_network_name = kwargs.get('social_network').name
            self.api_url = kwargs.get('social_network').apiUrl
            self.access_token = self.user_credentials.accessToken
            self.start_date_dt = None
        except Exception as e:
            error_message = e.message
            self.message_to_log.update({'error': error_message})
            log_exception(self.message_to_log)

    @abstractmethod
    def get_rsvps(self, event):
        """
        For a given event, we get the rsvps in this function. Child classes will
        implement the functionality
        :param event:
        :return:
        """
        pass

    def _process_rsvps(self):
        """
        We get events against a particular user_credential and then we go over
        each event one by one and do the following:
            a)- Get RSVPs of that event. This is done in the get_rsvps()
            method which gets RSVPs and attach them to rsvps list of dicts.
            This method get_rsvps() should be implemented by a child as
            implementation may vary across vendors.

        :return:
        """
        self.message_to_log.update({"functionName": "_process_rsvps()"})
        # get events from database where eventStartDate is greater than
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
                    if rsvps:
                        self.post_process_rsvp(rsvps)
                    elif rsvps is None:  # event has no RSVPs
                        break
                except Exception as e:
                    # Shouldn't raise an exception, just log it and move to process
                    # process next RSVP
                    error_message = e.message
                    self.message_to_log.update({'error': error_message})
                    log_exception(self.message_to_log)
        else:
            error_message = "There are no events for User in the Database"
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)

    def post_process_rsvp(self, rsvps):
        """
        This is the post processing once we get the rsvps of an event
        Here we do the followings
        a)- We move on to getting attendees using the given
            RSVPs (and those are in rsvps). get_attendees() call
            get_attendee() which should be implemented by a child.
        b)- We pick the source product of rsvp (e.g. meetup or eventbrite).
        c)- We store the source of candidate in candidate_source db table.
        d)- Once we have the list of attendees we call
            save_attendees_as_candidate() which take attendees (as
            given in self.attendees) and store each attendee as
            a candidate.
        e)- Finally we save the rsvp in rsvp and candiate_event_rsvp db tables.
        :param rsvps:
        :return:
        """
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

    def get_attendees(self, rsvps):
        """
        This calls get_attendee() which is usually implemented by the child
        because implementation may vary across different vendors.
        :param rsvps:
        :return:
        """
        attendees = map(self.get_attendee, rsvps)
        # only picks those attendees for which we are able to get data
        # rest attendees are logged and are not processed further
        attendees = filter(lambda attendee: attendee is not None, attendees)
        return attendees

    @abstractmethod
    def get_attendee(self, rsvp):
        """
        This function is used to get the data of candidate related
        to given rsvp. Child classes will implement the functionality
        :param rsvp:
        :return:
        """
        pass

    def pick_source_products(self, attendees):
        return map(self.pick_source_product, attendees)

    def pick_source_product(self, attendee):
        """
        Here we pick the id of source product by providing vendor name
        and appends it attendee object.
        :param attendee:
        :return:attendee
        """
        source_product = Product.get_by_name(self.social_network_name)
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
        returns attendee object.
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
        so that Get Talent user can see rsvps in Activity Feed.
        :param attendee:
        :return:
        """
        assert attendee.event.eventTitle is not None
        event_title = attendee.event.eventTitle
        gt_user_first_name = self.user_credentials.user.firstName
        gt_user_last_name = self.user_credentials.user.lastName
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
