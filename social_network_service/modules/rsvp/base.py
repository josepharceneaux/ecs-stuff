"""
This module contains RSVPBase class which contains common methods for all social networks that have RSVP
related functionality. It provides methods like
    - get_rsvps()
    - get_attendee()
    - process_rsvps()
    - save_attendee_as_candidate() etc.
"""

# Standard Library
import json
import requests
from abc import ABCMeta
from abc import abstractmethod
from datetime import datetime, timedelta

# Third Party
from redo import retry
from requests import codes

# Application Specific
from social_network_service.common.models.db import db
from social_network_service.modules.utilities import Attendee
from social_network_service.common.utils.auth_utils import refresh_token
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.inter_service_calls.activity_service_calls import add_activity
from social_network_service.common.models.rsvp import RSVP
from social_network_service.common.models.talent_pools_pipelines import TalentPool
from social_network_service.common.models.user import User, Token, UserSocialNetworkCredential
from social_network_service.common.models.misc import Product
from social_network_service.common.models.misc import Activity
from social_network_service.common.models.candidate import Candidate, EmailLabel, CandidateEmail
from social_network_service.common.models.candidate import CandidateSocialNetwork
from social_network_service.common.routes import UserServiceApiUrl, CandidateApiUrl
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.custom_exceptions import UserCredentialsNotFound, ProductNotFound
from social_network_service.social_network_app import logger, app
from social_network_service.common.constants import REQUEST_TIMEOUT


class RSVPBase(object):
    """
    - Social network has Events and an Event has RSVPs. This is the base class
        for handling RSVPs related to events of following social networks
            1-Meetup,
            2-Eventbrite,
            3-Facebook for now.
    - This class contains the common functionality and some abstract methods
        which are implemented by child classes.

    - It contains following methods to import RSVPs for an event of a
        particular social network:

    * __init__():
        This method is called by creating any child RSVP class object.
        It sets initial values for RSVP object e.g.
            It sets user, user_credentials, social network,
            headers (authentication headers), api_url, access_token,
            and start_date_dt.
            It also initializes rsvps list to empty list.

    * get_rsvps(self, event) : abstract
        All child classes need to implement this method to get RVSPs of a
        particular event from respective social network.

    * get_all_rsvps(self, events):
        This method loops over the list of events and call get_rsvps(event)
        on each event. It then appends rsvps of each event in self.rsvps.

    * process_rsvps(self, rsvps):
        This method loops over the list of rsvps. It picks one rsvp and call
        other methods to process and save them in database.

    * post_process_rsvp(self, rsvp):
        This method is made for future use if we have to do some post
        processing on saved rsvps.

    * get_attendee(self, rsvp): abstract
        This method creates and returns the attendee object (a placeholder object)
        by getting data about the candidate using respective API of social network.
        Attendee object contains the information about candidate like name,
         city, country etc).

    * pick_source_product(self, attendee):
        In this method, we get the source_product_id of the candidate and
        appends it in attendee object. Then we return the attendee object.

    * save_attendee_source(self, attendee):
        This method saves the source of attendee i.e. social_network_event_id
        of candidate. It then appends the social_network_event_id in attendee
        object and returns it.

    * save_attendee_as_candidate(self, attendee):
        Once we have the data for candidate, we save/update the data in
        candidate table in this method. It appends the id of candidate_id
        (id of candidate in db) in the attendee object and returns attendee
        object.

    * save_rsvp(self, attendee):
        In this method, we extract the data of RSVP from attendee object
        and save/update that data in db table rsvp.

    * save_rsvp_in_activity_table(self, attendee):
        This method adds/update an entry for each rsvp in db table activity.
        From this table data, user can see the activity feed on getTalent
        website.

    ** How to incorporate new social network **
    .. Adding RSVP code for a Social network::

        If we need to implement a new social network say 'xyz', for
        which we have Events, we will need to create a new file as
        social_network_service/rsvp/xyz.py.
        In "xyz.py" we will have a class XYZ() inherited from RSVPBase class.
        XYZ() class will have the implementation of abstract methods like

        1- get_rsvps() to get RSVPs of an event present on xyz website

        2- get_attendee() to get information of candidate who has responded
            on an event
        etc.

        XYZ() can also have any other method according to its need.
        **See Also**
        .. seealso:: Eventbrite class inside
                    social_network_service/rsvp/eventbrite.py

    - To understand how the RSVP importer works, we have an example here.
        We make the object of this class while importing RSVPs both through
        social_network.

        :Example:

        If we are importing rsvps of social network meetup, then we create
        RSVP class object in EventBase class method get_rsvps() as

        sn_rsvp_obj = sn_rsvp_class(social_network=self.social_network,
                                    headers=self.headers,
                                    user_credentials=user_credentials)

        Then we call get_all_rsvps() on sn_rsvp_obj by passing events in
        parameters as follow

            self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)

        This gives us all the RSVPs of events of a particular user.
        Once we have all rsvps to process, we call process_rsvps() on
        sn_rsvp_obj as

            sn_rsvp_obj.process_rsvps(self.rsvps)

        Above loops through each rsvp in self.rsvps and passes it in
        post_process_rsvps() which serves the processing to save
        rsvp in database.

    **See Also**
        .. seealso:: process_events_rsvps() method in EventBase class inside
                    social_network_service/event/base.py for more insight.
    """
    __metaclass__ = ABCMeta

    def __init__(self, user_credentials, headers, social_network, *args, **kwargs):
        if not isinstance(user_credentials, UserSocialNetworkCredential):
            raise UserCredentialsNotFound('User Credentials are empty/none for requesting user')
        self.user_credentials = user_credentials
        self.user = User.get_by_id(self.user_credentials.user_id)
        self._get_valid_access_token()
        self.headers = headers
        self.social_network = social_network
        self.api_url = self.social_network.api_url
        self.access_token = self.user_credentials.access_token
        self.start_date_dt = None
        self.rsvps = []
        self.flag_create_activity = True
        self.rsvp_via_importer = True

    def _get_valid_access_token(self):
        """
        This refreshes access_token of user if expired and returns it. For that send request to auth service and
        request a fresh access_token.
        """
        user_token = retry(self._get_user_token, sleeptime=5, attempts=6, sleepscale=1,
                           retry_exceptions=(InternalServerError,))
        is_expired = user_token.expires - timedelta(seconds=REQUEST_TIMEOUT) < datetime.utcnow()
        return refresh_token(user_token.access_token) if is_expired else user_token.access_token

    def _get_user_token(self):
        """
        This gets the token object of user from database table Token
        """
        db.session.commit()  # Need to add as new tokens are saved in Auth Service, so session here gets old with
        # respect to those changes
        user_token = Token.get_by_user_id(self.user_credentials.user_id)
        if not user_token.access_token:
            raise InternalServerError('access_token not found for user(id:%s)' % self.user_credentials.user_id)
        return user_token

    @abstractmethod
    def get_rsvps(self, event):
        """
        :param event: event in getTalent database
        :type event: common.models.event.Event

        - For a given event, we get the rsvps in this method. This method
        should be implemented by a child as implementation may vary across
        social networks.

        - This method is called from get_all_rsvps() defined in RSVPBase class
            inside social_network_service/rsvp/base.py. We use this method
            while importing RSVPs through social network manager.

        :Example:

            rsvps = self.get_rsvps(event)

        **See Also**
        .. seealso:: get_all_rsvps() method in RSVPBase class inside
        social_network_service/rsvp/base.py

        :return: It returns the list of rsvps for a particular event where
        each rsvp is likely the response from social network in dict format.
        """
        pass

    def get_all_rsvps(self, events):
        """
        :param events: events contains all the events of a particular
                       user present in database table "event".
        :type events: list

        ** Working **
            - We go over each event one by one and get RSVPs of that event.
                This is done in the get_rsvps() method which fetches RSVPs
                and attach them to rsvps list of dicts.

        :Example:

        If we are importing rsvps of social network meetup, then we create
        RSVP class object in EventBase class method process_events_rsvps() as

        sn_rsvp_obj = sn_rsvp_class(social_network=self.social_network,
                                    headers=self.headers,
                                    user_credentials=user_credentials)

        Then we call get_all_rsvps() on sn_rsvp_obj by passing events in
        parameters as follow

            self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)

        :return: It appends rsvps of all events of a particular user in
            self.rsvps and returns it.

        - We use this method inside process_events_rsvps() defined in
            EventBase class inside social_network_service/event/base.py.

        - We use this method while importing RSVPs through social_network either by direct hitting endpoint or
        by running an hourly job scheduled by scheduler service.
        **See Also**
            .. seealso:: process_events_rsvps() method in EventBase class
            inside social_network_service/event/base.py
        """
        if events:
            logger.info('Getting RSVPs for events of %s(UserId: %s) from %s website.'
                        % (self.user.name, self.user.id, self.social_network.name))
            for event in events:
                # events is a list of dicts where each dict is likely a
                # response return from the database.
                # We pick one event from events_list, and get its rsvps
                # from respective social network.
                try:
                    rsvps = self.get_rsvps(event)
                    # rsvps is a list of dicts, where each dict is likely a response returned from the
                    # social network side.
                    if rsvps:
                        # appends RSVPs of all events in self.rsvps
                        self.rsvps += rsvps
                except Exception as error:
                    # Shouldn't raise an exception, just log it and move to get RSVPs of next event
                    logger.exception('get_all_rsvps: user_id: %s, event_id: %s, social network: %s(id:%s)'
                                     % (self.user.id, event.id, self.social_network.name, self.social_network.id))
                    if hasattr(error, 'response'):
                        if error.response.status_code == codes.UNAUTHORIZED:
                            # Access token is Invalid, Stop the execution.
                            break
            logger.info('There are %d RSVPs to process for events of %s(UserId: %s).'
                        % (len(self.rsvps), self.user.name, self.user.id))
        return self.rsvps

    def process_rsvps(self, rsvps):
        """
        :param rsvps: rsvps contains rsvps of all events of a particular
                      user.
        :type rsvps: list

        - This method picks an rsvp from "rsvps" and pass it to
            post_process_rsvp()

        - This method is called from process_events_rsvps() defined in
            EventBase class inside social_network_service/event/base.py.

        - We use this method while importing RSVPs via social network manager.

        :Example:
            - sn_rsvp_obj = sn_rsvp_class(social_network=self.social_network,
                            headers=self.headers,
                            user_credentials=user_credentials)
            - self.rsvps = sn_rsvp_obj.get_all_rsvps(self.events)
            - sn_rsvp_obj.process_rsvps(self.rsvps)

        **See Also**
        .. seealso:: process_events_rsvps() method in EventBase class
            social_network_service/event/base.py
        """
        processed_rsvps = []
        total_rsvps_count = len(rsvps)
        for rsvp in rsvps:
            # Here we pick one RSVP from rsvps and start doing processing on it. If we get an error while processing
            # an RSVP, we simply log the error and move to process next RSVP.
            processed_rsvps.append(self.post_process_rsvp(rsvp))
        saved_rsvps_count = len(filter(None, processed_rsvps))
        failed_rsvps_count = total_rsvps_count - saved_rsvps_count
        if total_rsvps_count:
            logger.info('''
                        process_rsvps: RSVPs for events of %s(UserId:%s) have been processed.
                        Successfully saved:%d, Failed:%d. Social network:%s
                        '''
                        % (self.user.name, self.user.id, saved_rsvps_count, failed_rsvps_count,
                           self.social_network.name))

    def post_process_rsvp(self, rsvp):
        """
        :param dict rsvp: is likely the response from social network API.

        ** Working **
             - Here we do the following steps
                a)- We move on to get attendee using the given rsvp by
                    get_attendees() call. "attendees" is a utility object we
                    share in calls that contains pertinent data. get_attendee()
                    should be implemented by a child.
                b)- We pick the source product of RSVP (e.g. meetup or
                    eventbrite).
                c)- We store the source of candidate in candidate_source db
                    table.
                d)- Once we have the attendees data we call
                    save_attendee_as_candidate() which stores each attendee as
                    a candidate.
                e)- Finally we save the RSVP in following tables
                    1- rsvp
                    3- Activity

        - This method is called from process_rsvps() defined in
            RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network
        # TODO: Through nightly script which fetches data from different social networks

        :Example:
            - rsvp_obj = Meetup(social_network=self.social_network,
                            headers=self.headers,
                            user_credentials=user_credentials)
            - event = Event.get_by_id(1)
            - rsvps = rsvp_obj.get_rsvps(event)
            - rsvp_obj.post_process_rsvps(rsvps[0])

        **See Also**
        .. seealso:: process_events_rsvps() method in EventBase class
            social_network_service/event/base.py
        """
        try:
            attendee = self.get_attendee(rsvp)
            if not attendee:
                logger.info('Attendee object couldn\'t be created because event is not imported yet. RSVP data: %s'
                            % rsvp)
                return
            # following picks the source product id for attendee
            attendee = self.pick_source_product(attendee)
            # following will store candidate info in attendees
            attendee = self.save_attendee_source(attendee)
            # following will store candidate info in attendees
            attendee = self.save_attendee_as_candidate(attendee)
            # following call will store rsvp info in attendees
            attendee = self.save_rsvp(attendee)
            # finally we store info in table activity
            attendee = self.save_rsvp_in_activity_table(attendee)
            return attendee
        except Exception:
            # Shouldn't raise an exception, just log it and move to process next RSVP
            logger.exception('post_process_rsvps: user_id: %s, RSVP data: %s, social network: %s(id:%s)'
                             % (self.user.id, rsvp, self.social_network.name, self.social_network.id))

    @abstractmethod
    def get_attendee(self, rsvp):
        """
        :param dict rsvp: is likely the response from social network API.

        - This function is used to get the data of candidate related
          to given rsvp. It attaches all the information in attendee object.
          attendees is a utility object we share in calls that contains
          pertinent data. Child classes will implement the functionality.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network

        :Example:

            attendee = self.get_attendee(rsvp)

        **See Also**
            .. seealso:: process_rsvps() method in RSVPBase class inside
            social_network_service/rsvp/base.py
        :return attendee:
        :rtype: object
        """
        pass

    def pick_source_product(self, attendee):
        """
        :param attendee: attendees is a utility object we share in calls that
                         contains pertinent data.
        :type attendee: object of class Attendee defined in utilities.py

        - Here we pick the id of source product by providing social network
            name and appends the id of matched record in attendee object. If
            no record is found, we log and raise the error.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network

        :Example:

            attendee = self.pick_source_product(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: object
        """
        source_product = Product.get_by_name(self.social_network.name)
        if source_product:
            attendee.source_product_id = source_product.id
        else:
            raise ProductNotFound('No product found for Social Network %s. User Id: %s'
                                  % (self.social_network.name, self.user.id))
        return attendee

    def save_attendee_source(self, attendee):
        """
        :param attendee: attendees is a utility object we share in calls that
                 contains pertinent data.
        :type attendee: object of class Attendee defined in utilities.py

        - This method checks if the event is present in candidate_source db
         table. If does not exist, it adds record, otherwise updates the
         record. It then appends id of source in attendee object to be saved in
         candidate table.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network

        :Example:

            attendee = self.save_attendee_source(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: Attendee
        """
        headers = {'Authorization': 'Bearer {}'.format(self._get_valid_access_token()),
                   "Content-Type": "application/json"}
        attendee.event.description = attendee.event.description[:1000].encode('utf-8') if attendee.event.description \
            else 'Not given'
        candidate_source = {
            "source": {
                "description": attendee.event.description,
                "notes": attendee.event.title
            }
        }
        response = http_request('POST', UserServiceApiUrl.DOMAIN_SOURCES, headers=headers,
                                data=json.dumps(candidate_source))
        # Source already exists
        if response.status_code == requests.codes.bad:
            attendee.candidate_source_id = response.json()['error']['source_id']
        elif response.status_code != requests.codes.created:
            logger.exception(response.text)
            raise InternalServerError(error_message="Error while creating candidate source")
        else:
            attendee.candidate_source_id = response.json()['source']['id']

        return attendee

    def save_attendee_as_candidate(self, attendee):
        """
        :param attendee: attendees is a utility object we share in calls that
         contains pertinent data.
        :type attendee: object of class Attendee defined in utilities.py

        - This method adds the attendee as a new candidate if it is not present
         in the database already, otherwise it updates the previous record. It
         then appends the candidate_id to the attendee object and add/updates record in
         candidate_social_network db table. It then returns attendee object.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network
        :Example:

            attendee = self.save_attendee_as_candidate(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: Attendee
        """
        candidate_in_db = None
        request_method = 'post'
        domain_id = User.get_domain_id(attendee.gt_user_id)
        candidate_by_email = CandidateEmail.get_email_in_users_domain(domain_id, attendee.email)
        if candidate_by_email:
            candidate_in_db = candidate_by_email.candidate
        if not candidate_in_db:
            # TODO: Need to handle multiple sources per candidate
            candidate_in_db = Candidate.filter_by_keywords(first_name=attendee.first_name,
                                                           last_name=attendee.last_name,
                                                           source_id=attendee.candidate_source_id,
                                                           source_product_id=attendee.source_product_id)

            if candidate_in_db:
                candidate_in_db = candidate_in_db[0]
                # Check if candidate's domain is same as user's domain
                if not candidate_in_db.user.domain_id == domain_id:
                    candidate_in_db = None

        # To create candidates, user must have be associated with talent_pool
        talent_pools = TalentPool.filter_by_keywords(user_id=attendee.gt_user_id)
        talent_pool_ids = map(lambda talent_pool: talent_pool.id, talent_pools)

        if not talent_pool_ids:
            raise InternalServerError("save_attendee_as_candidate: user doesn't have any talent_pool")

        # Create data dictionary
        data = {'first_name': attendee.first_name,
                'last_name': attendee.last_name,
                'source_id': attendee.candidate_source_id,
                'source_product_id': attendee.source_product_id,
                'talent_pool_ids': dict(add=talent_pool_ids)
                }
        social_network_data = {
            'name': attendee.event.social_network.name,
            'profile_url': attendee.social_profile_url
        }

        # Update if already exist
        if candidate_in_db:
            candidate_id = candidate_in_db.id
            data.update({'id': candidate_id})
            request_method = 'patch'
            # Get candidate's social network if already exist
            candidate_social_network_in_db = \
                CandidateSocialNetwork.get_by_candidate_id_and_sn_id(candidate_id, attendee.social_network_id)
            if candidate_social_network_in_db:
                social_network_data.update({'id': candidate_social_network_in_db.id})

        if attendee.email:
            data.update({'emails': [{'address': attendee.email,
                                     'label': EmailLabel.PRIMARY_DESCRIPTION,
                                     'is_default': True
                                     }]
                         })
        # Update social network data to be sent with candidate
        data.update({'social_networks': [social_network_data]})

        headers = {'Authorization': 'Bearer {}'.format(self._get_valid_access_token()),
                   "Content-Type": "application/json"}

        resp = http_request(request_method, url=CandidateApiUrl.CANDIDATES, headers=headers,
                            data=json.dumps(dict(candidates=[data])), app=app)
        data_resp = resp.json()
        if resp.status_code not in [codes.CREATED, codes.OK]:
            error_message = 'save_attendee_as_candidate: candidate creation failed. Error:%s' % data_resp
            logger.error(error_message)
            raise InternalServerError(error_message)
        attendee.candidate_id = data_resp['candidates'][0]['id']
        return attendee

    def save_rsvp(self, attendee):
        """
        :param attendee: attendees is a utility object we share in calls that
         contains pertinent data.
        :type attendee: object of class Attendee defined in utilities.py

        - It finds the matched record in database. If record is already present
        in db, it updates the previous record, otherwise it adds a new record.
        It then appends the id of record in attendee object and returns
        attendee object as well.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network

        :Example:

            attendee = self.save_rsvp(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: Attendee
        """

        rsvp_in_db = RSVP.get_by_vendor_rsvp_id_candidate_id_vendor_id_event_id(attendee.vendor_rsvp_id,
                                                                                attendee.candidate_id,
                                                                                attendee.social_network_id,
                                                                                attendee.event.id)
        data = {'candidate_id': attendee.candidate_id, 'event_id': attendee.event.id,
                'social_network_rsvp_id': attendee.vendor_rsvp_id, 'social_network_id': attendee.social_network_id,
                'status': attendee.rsvp_status, 'datetime': attendee.added_time
        }
        if rsvp_in_db:
            rsvp_in_db.update(**data)
            rsvp_id_db = rsvp_in_db.id
            self.flag_create_activity = False
        else:
            rsvp = RSVP(**data)
            RSVP.save(rsvp)
            rsvp_id_db = rsvp.id
        attendee.rsvp_id = rsvp_id_db
        return attendee

    def save_rsvp_in_activity_table(self, attendee):
        """
        :param attendee: attendees is a utility object we share in calls that
         contains pertinent data.
        :type attendee: object of class Attendee defined in utilities.py

        - Once rsvp is stored in all required tables, here we update Activity
            table so that getTalent user can see rsvps in Activity feed.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network

        :Example:

            attendee = self.save_rsvp_in_activity_table(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: Attendee
        """
        assert attendee.event.title is not None
        event_title = attendee.event.title
        gt_user_first_name = self.user.first_name
        gt_user_last_name = self.user.last_name

        first_name = attendee.first_name
        last_name = attendee.last_name
        params = {'firstName': first_name,
                  'lastName': last_name,
                  'eventTitle': event_title,
                  'response': attendee.rsvp_status,
                  'img': attendee.vendor_img_link,
                  'creator': '%s' % gt_user_first_name + ' %s'
                                                         % gt_user_last_name}
        if self.flag_create_activity:
            add_activity(user_id=attendee.gt_user_id,
                         activity_type=Activity.MessageIds.RSVP_EVENT,
                         source_id=attendee.rsvp_id,
                         source_table=RSVP.__tablename__,
                         params=json.dumps(params))
        return attendee
