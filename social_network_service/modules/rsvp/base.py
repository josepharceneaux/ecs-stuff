"""
This module contains RSVPBase class which contains common methods for
all social networks that have RSVP related functionality. It provides methods
like get_rsvps(), get_attendee(), process_rsvps(),save_attendee_as_candidate()
etc.
"""

# Standard Library
import json
from abc import ABCMeta
from abc import abstractmethod

# Third Party libraries
import requests

# Application Specific
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.inter_service_calls.activity_service_calls import add_activity
from social_network_service.common.inter_service_calls.candidate_service_calls import \
    create_candidates_from_candidate_api
from social_network_service.common.models.rsvp import RSVP
from social_network_service.common.models.talent_pools_pipelines import TalentPool
from social_network_service.common.models.user import User, Token
from social_network_service.common.models.misc import Product
from social_network_service.common.models.misc import Activity
from social_network_service.common.models.candidate import Candidate
from social_network_service.common.models.candidate import CandidateSocialNetwork
from social_network_service.common.routes import UserServiceApiUrl
from social_network_service.custom_exceptions import UserCredentialsNotFound, ProductNotFound
from social_network_service.social_network_app import logger


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
        manager and webhook.

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

    def __init__(self, *args, **kwargs):
        # TODO: we should check isinstance here as we are getting object properties below
        if kwargs.get('user_credentials'):
            self.user_credentials = kwargs.get('user_credentials')
            # TODO: Not sure whats session expire issue. (Basit)
            # To resolve session expire issue, save the fields in a dict
            self.user_credentials_dict = dict(id=self.user_credentials.id,
                                              access_token=self.user_credentials.access_token,
                                              refresh_token=self.user_credentials.refresh_token,
                                              social_network_id=self.user_credentials.social_network_id,
                                              user_id=self.user_credentials.user_id)
            self.user = User.get_by_id(self.user_credentials_dict['user_id'])
        else:
            raise UserCredentialsNotFound('User Credentials are empty/none')

        self.headers = kwargs.get('headers')
        self.social_network = kwargs.get('social_network')
        self.api_url = kwargs.get('social_network').api_url
        self.access_token = self.user_credentials_dict['access_token']
        self.start_date_dt = None
        self.rsvps = []

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

        - We use this method while importing RSVPs via social network manager.

        **See Also**
            .. seealso:: process_events_rsvps() method in EventBase class
            inside social_network_service/event/base.py
        """
        if events:
            logger.debug('Getting RSVPs for events '
                         'of %s(UserId: %s) from %s website.'
                         % (self.user.name, self.user.id,
                            self.social_network.name))
            for event in events:
                # events is a list of dicts where each dict is likely a
                # response return from the database.
                # We pick one event from events_list, and get its rsvps
                # from respective social network.
                try:
                    rsvps = self.get_rsvps(event)
                    # rsvps is a list of dicts, where each dict is likely a
                    # response returned from the social network side.
                    if rsvps:
                        # appends rsvps of all events in self.rsvps
                        self.rsvps += rsvps
                except Exception as error:
                    # Shouldn't raise an exception, just log it and move to
                    # get RSVPs of next event
                    logger.exception('get_all_rsvps: user_id: %s, event_id: %s, '
                                     'social network: %s(id:%s)'
                                     % (self.user.id, event.id, self.social_network.name,
                                        self.social_network.id))
                    if hasattr(error, 'response'):
                        if error.response.status_code == 401:
                            # Access token is Invalid, Stop the execution.
                            break
            logger.debug('There are %d RSVPs to process for events of '
                         '%s(UserId: %s).' % (len(self.rsvps), self.user.name,
                                              self.user.id))
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
        for rsvp in rsvps:
            # Here we pick one RSVP from rsvps and start doing
            # processing on it. If we get an error while processing
            # an RSVP, we simply log the error and move to process
            # next RSVP.
            self.post_process_rsvp(rsvp)
        if rsvps:
            logger.debug('%d RSVPs for events of %s(UserId: %s) have been '
                         'processed and saved successfully in database.'
                         % (len(rsvps), self.user.name, self.user.id))

    def post_process_rsvp(self, rsvp):
        """
        :param rsvp: is likely the response from social network API.
        :type rsvp: dict

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

        - We use this method while importing RSVPs via social network manager
            or webhook.

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
        except:
            # Shouldn't raise an exception, just log it and move to
            # process next RSVP
            logger.exception('post_process_rsvps: user_id: %s, RSVP data: %s, '
                             'social network: %s(id:%s)'
                             % (self.user.id, rsvp, self.social_network.name,
                                self.social_network.id))

    @abstractmethod
    def get_attendee(self, rsvp):
        """
        :param rsvp: rsvp is likely the response we get from specific social
            network API.
        :type rsvp: dict

        - This function is used to get the data of candidate related
          to given rsvp. It attaches all the information in attendee object.
          attendees is a utility object we share in calls that contains
          pertinent data. Child classes will implement the functionality.

        - This method is called from process_rsvps() defined in
          RSVPBase class inside social_network_service/rsvp/base.py.

        - We use this method while importing RSVPs through social network
          manager or webhook.

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
          manager or webhook.

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
            raise ProductNotFound('No product found for Social Network '
                                  '%s. User Id: %s'
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
          manager or webhook.

        :Example:

            attendee = self.save_attendee_source(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: object
        """
        # TODO: Update rtype to be Attendee (import from utilities) here and every where else
        # TODO: Now we have removed use of self. It should be static now.

        # TODO--please ensure the comments of this method still reflect the reality
        token = Token.get_by_user_id(attendee.gt_user_id)
        # TODO: Shouldn't we raise if token is not found? rather than requesting candidate_service with None token?(Basit)
        # TODO--not sure but is not None a problem in the headers?
        headers = {'Authorization': 'Bearer {}'.format(token.access_token if token else None),
                   "Content-Type": "application/json"}

        candidate_source = {
            "source": {
                "description": attendee.event.description[:495] if attendee.event.description else None,
                "notes": attendee.event.title
            }
        }
        # TODO: why not http_request here?
        response = requests.post(UserServiceApiUrl.DOMAIN_SOURCES,
                                 headers=headers,
                                 data=json.dumps(candidate_source))

        # Source already exist
        if response.status_code == 400:
            attendee.candidate_source_id = response.json()['error']['source_id']
        elif response.status_code != 201:
            logger.exception(response.text)
            raise InternalServerError(error_message="Error while creating candidate source")
        else:
            attendee.candidate_source_id = response.json()['source']['id']

        return attendee

    @staticmethod
    def save_attendee_as_candidate(attendee):
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
          manager or webhook.

        :Example:

            attendee = self.save_attendee_as_candidate(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: object
        """
        # TODO: unused line (Basit)
        # TODO--kindly ensure the above comments reflect the reality
        #TODO--following isn't being used anywhere
        newly_added_candidate = 1  # 1 represents entity is new candidate
        candidate_in_db = \
            Candidate.get_by_first_last_name_owner_user_id_source_id_product(
                attendee.first_name,
                attendee.last_name,
                attendee.gt_user_id,
                attendee.candidate_source_id,
                attendee.source_product_id)

        # TODO--kindly add comments why the need of talent pool id
        talent_pools = TalentPool.get_by_user_id(attendee.gt_user_id)
        talent_pool_ids = map(lambda talent_pool: talent_pool.id, talent_pools)
        # TODO: Log useful data. e.g., user_id, sn_id etc (Basit)
        # TODO--what if talent_pool_ids has [None, '', 0]. Please cater this scenario when you check for None. Yes, assume this may happen
        if not talent_pool_ids:
            raise InternalServerError("save_attendee_as_candidate: user doesn't have any talent_pool")

        # Create data dictionary
        data = {'first_name': attendee.first_name,
                'last_name': attendee.last_name,
                'source_id': attendee.candidate_source_id,
                'talent_pool_ids': dict(add=talent_pool_ids)
                }
        # TODO: pep8 violation
        social_network_data = {
             'name': attendee.event.social_network.name,
             'profile_url': attendee.social_profile_url
        }

        # Update if already exist
        if candidate_in_db:
            candidate_id = candidate_in_db.id
            data = dict(candidates=[data])

            # Get candidate's social network if already exist
            # TODO: pep8 violation (Basit)
            candidate_social_network_in_db = \
                CandidateSocialNetwork.get_by_candidate_id_and_sn_id(
                    candidate_id, attendee.social_network_id)
            if candidate_social_network_in_db:
                social_network_data.update({'id': candidate_social_network_in_db.id})

        if attendee.email:
            data.update({'emails': [{'address': attendee.email,
                                     'label': 'Primary',
                                     'is_default': True}]})

        # Update social network data to be sent with candidate
        data.update({'social_networks': [social_network_data]})
        # TODO: we are getting token again. I think make it property of Attendee object.
        token = Token.get_by_user_id(attendee.gt_user_id)
        # TODO: Isn't this creating every time? How will it update if candidate exists? i.e. patch request.
        response = create_candidates_from_candidate_api(oauth_token=token.access_token if token else None,
                                                        data=dict(candidates=[data]),
                                                        return_candidate_ids_only=True)
        # TODO: In case of update, we will already have id. (Basit)
        # TODO --is the response being validated
        # Get created candidate id
        candidate_id = response[0]
        attendee.candidate_id = candidate_id

        return attendee

    @staticmethod
    def save_rsvp(attendee):
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
          manager or webhook.

        :Example:

            attendee = self.save_rsvp(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: object
        """
        rsvp_in_db = \
            RSVP.get_by_vendor_rsvp_id_candidate_id_vendor_id_event_id(
            attendee.vendor_rsvp_id,
            attendee.candidate_id,
            attendee.social_network_id,
            attendee.event.id)
        data = {
            'candidate_id': attendee.candidate_id,
            'event_id': attendee.event.id,
            'social_network_rsvp_id': attendee.vendor_rsvp_id,
            'social_network_id': attendee.social_network_id,
            'status': attendee.rsvp_status,
            'datetime': attendee.added_time
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
          manager or webhook.

        :Example:

            attendee = self.save_rsvp_in_activity_table(attendee)

        **See Also**
            .. seealso:: process_rsvps() method in EventBase class
        :return attendee:
        :rtype: object
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
        # TODO: why aren't we checking that activity has already been created? IMOit will create multiple activities
        # TODO: for a particular event.
        add_activity(user_id=attendee.gt_user_id,
                     activity_type=Activity.MessageIds.RSVP_EVENT,
                     source_id=attendee.rsvp_id,
                     source_table=RSVP.__tablename__,
                     params=json.dumps(params))
        return attendee
