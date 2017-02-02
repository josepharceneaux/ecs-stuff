"""
This module contains SocialNetworkBase class which provides common methods for
all social networks like get_access_and_refresh_token(), validate_access_token(),
refresh_access_token(), get_member_id() and save_user_credentials_in_db() etc.
"""

# Standard Library
from abc import ABCMeta

# Third Party
import requests
from requests import codes

# Application Specific
from social_network_service.common.models.venue import Venue
from social_network_service.common.models.db import db
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.common.utils.validators import raise_if_not_positive_int_or_long
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls
from social_network_service.modules.constants import EVENT, RSVP
from social_network_service.modules.urls import get_url
from social_network_service.modules.utilities import get_class
from social_network_service.modules.utilities import log_error
from social_network_service.common.models.user import User
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.social_network_app import logger, app
from social_network_service.custom_exceptions import *
from social_network_service.common.error_handling import InvalidUsage, InternalServerError


class SocialNetworkBase(object):
    """
    - This is the base class related to social networks. It contains the
        common functionality and some abstract methods which are implemented
        by child classes.

    - Currently we have the implementation for following social networks.

        1- Meetup
        2- Eventbrite
        3- Facebook
        4- Twitter (Only authentication part for now)

    - Usually API of any social network requires user permission to gain access
        of user's account. Once user allows access, we get an access token to
        play with the API of that social network. This access token expires in
        1- One hour (Meetup)
        2- Not expires until account password is changed (Eventbrite)
        3- Sixty days (Facebook).
        4- Not expires until user removes getTalent app from allowed apps (Twitter)

    - Before going to event part, we first check the validity of access token,
        and try to refresh it without user interaction inside __init__().
        Currently it is refreshed for Meetup successfully. For this task we
        have the methods

            1- validate_token() and 2- refresh_access_token()

        in base and child classes.

        validate_token() implemented in child, sets the value of variable
        self.api_relative_url. It then calls super class method to make HTTP
        request on
            url = self.social_network.api_url + self.api_relative_url
        (This will evaluate in case of Meetup as
            url = 'https://api.meetup.com/2' + '/member/self')

        If we get response status in range 2xx, then access token is valid.
        Otherwise we implement functionality in child method
        **refresh_access_token()** according to the social network. On success we
        return True, otherwise False.

    - Social Networks and Events has 'has a' relationship. All the
        functionality related to events is inside social_network_service/event/.

    ** How to incorporate new social network **
    .. Adding new social network::

        One can add new social network say "xyz" to work with by implementing
        auth related functionality in social_network_service/xyz.py.
        "xyz.py" will have a class XYZ() inherited from SocialNetworkBase
        and will have the methods like

        1- get_access_and_refresh_token() to get access token (and refresh
            token if "xyz" has any)

        2- validate_access_token() to check the validity of access token present
            in getTalent db table 'user_social_network_credential'

        3- refresh_access_token() (if "xyz" social network allows to refresh
            access token without user interaction)
        etc.

        **See Also**
        .. seealso:: Meetup class inside social_network_service/meetup.py.

        If 'xyz' social network has Events, the functionality of handling
        Events will go inside social_network_service/event/xyz.py.
        **See Also**
        .. seealso:: EventBase class to get insight how the event handling will be
         done. (social_network_service/event/base.py).
        .. seealso:: Meetup class inside social_network_service/event/meetup.py.

    This class contains following methods:

    * __init__():
        This method is called by creating any child RSVP class object.
        - It takes "user_id" as keyword argument.
        - It sets initial values for its object e.g.
            It sets user, user_credentials, social network,
            headers (authentication headers), api_url, access_token.

    * process(self, mode, user_credentials=None):
        This method is called by the social network manager while importing
        events or RSVPs. It takes "mode" as parameter and based
        on its value, it calls the process_events() or process_event_rsvps() to
        import events and rsvps respectively.

    * get_access_and_refresh_token(cls, data):
        When user tries to connect to a social network (eventbrite and meetup
        for now), then after successful redirection, social network returns a
        "code" to exchange for access and refresh tokens. We exchange "code"
        for access and refresh tokens in this method.

    * get_member_id(self, data):
        This method is used to get the member id of getTalent user on provided
        social network. e.g. profile id of user on Facebook.

    * validate_token(self, payload=None):
        This method is made for validation of access token. It returns True if
        access token is valid and False otherwise.

    * refresh_access_token(self):
        If access token has expired, any child can implement this method to
        refresh access token accordingly,

    * validate_and_refresh_access_token(self):
        This uses validate_token() to validate and refresh_access_token()
        to refresh access token.

    * save_user_credentials_in_db(user_credentials):
        Once we have the access token of user for some social network, we save
        this in user_credentials db table in this method.

    - This class does the authentication of access token and calls required
        methods to import/create events or import RSVPs

    - An example of importing events of Meetup is given below:
        :Example:

        If we are importing events of Meetup social network, then we do the
            following steps:

        1- Create class object
            from social_network_service.meetup import Meetup
            sn = Meetup(user_id=1)

        2- Call method process()
            sn.process('event', user_credentials=user_credentials)

        3- Create EventClass object
            sn_event_obj = event_class(user_credentials=user_credentials,
                                           social_network=self.social_network,
                                           headers=self.headers)
        4- Get events of user from API of social network
            self.events = sn_event_obj.get_events()

        5- Finally call process_events(self.events) to process and save events
            in database.
                sn_event_obj.process_events(self.events)

    **See Also**
        .. seealso:: start() function in social network manager.
        (social_network_service/manager.py)

        .. seealso:: process_event() function in social network manager.
        (social_network_service/manager.py)
    """
    __metaclass__ = ABCMeta

    def __init__(self,  user_id, social_network_id=None, validate_credentials=True, validate_token=True,
                 exclude_fields=()):
        """
        - This sets the user's credentials as base class property so that it can be used in other classes.
        - We also check the validity of access token and try to refresh it in case it has expired.
        :param int|long user_id: Id of User
        :param int|long|None social_network_id: Social Network Id
        :param bool validate_credentials: If True, this will validate the credentials of user for given social network.
        :param bool validate_token: If True, this will validate auth token of user for given social network.
        """
        self.events = []
        self.api_relative_url = None
        self.user, self.social_network = self.get_user_and_social_network(user_id, social_network_id)
        self.api_url = self.social_network.api_url
        self.user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(self.user.id,
                                                                                              self.social_network.id)
        if validate_credentials:
            if not self.user_credentials:
                raise UserCredentialsNotFound('UserSocialNetworkCredential for social network '
                                              '%s and User Id %s not found in db.'
                                              % (self.__class__.__name__, self.user.id))
            data = {
                "access_token": self.user_credentials.access_token,
                "gt_user_id": self.user_credentials.user_id,
                "social_network_id": self.social_network.id,
                "auth_url": self.social_network.auth_url
            }
            # checks if any field is missing for given user credentials
            items = [value for key, value in data.iteritems() if key not in exclude_fields]

            if all(items):
                self.auth_url = data['auth_url']
                self.gt_user_id = data['gt_user_id']
                self.social_network_id = data['social_network_id']
                self.access_token = data['access_token']
            else:
                # gets fields which are missing
                items = [key for key, value in data.iteritems() if key not in exclude_fields and not value]

                data_to_log = {'user_id': self.user.id, 'missing_items': items}
                # Log those fields in error which are not present in Database
                error_message = "User id: %(user_id)s\n Missing Item(s) in user's " \
                                "credential: %(missing_items)s\n" % data_to_log
                raise MissingFieldsInUserCredentials('API Error: %s' % error_message)
            # Eventbrite and meetup social networks take access token in header
            # so here we generate authorization header to be used by both of them
            self.headers = {'Authorization': 'Bearer ' + self.access_token}
            # token validity is checked here. If token is expired, we refresh it
            # here and save new access token in database.
            if validate_token:
                self.access_token_status = self.validate_and_refresh_access_token()
            else:
                self.access_token_status = True
            if not self.access_token_status:
                # Access token has expired. Couldn't refresh it for given
                # social network.
                logger.info('__init__: Access token has expired. Please connect with %s again from "Profile" page. '
                            'user_id: %s' % (self.social_network.name, self.user.id))
                raise AccessTokenHasExpired('Access token has expired for %s' % self.social_network.name)
            self.start_date_dt = None
            self.webhook_id = None
            if not self.user_credentials.member_id and validate_token:
                # gets and save the member id of gt-user
                self.get_member_id()

    def get_user_and_social_network(self, user_id, social_network_id=None):
        """
        This gets the User object and social network object from database.
        :param int | long user_id: Id of user
        :param int | long | None social_network_id: Id of SocialNetwork object
        :rtype: tuple
        """
        raise_if_not_positive_int_or_long(user_id)
        user = User.query.get(user_id)
        if not user:
            raise NoUserFound("No User found in database with id %s." % user_id)
        if social_network_id:
            raise_if_not_positive_int_or_long(social_network_id)
            social_network = SocialNetwork.get_by_id(social_network_id)
        else:
            social_network = SocialNetwork.get_by_name(self.__class__.__name__)
        return user, social_network

    def process(self, mode, user_credentials=None, **kwargs):
        """
        :param mode: mode is either 'event' or 'rsvp.
        :param user_credentials: are the credentials of user for
                                    a specific social network in db.
        :type mode: str
        :type user_credentials: common.models.user.UserSocialNetworkCredential

        - Depending upon the mode, here we make the objects of required
            classes (Event Class or RSVP class) and call required methods on
            those objects for importing events or rsvps.

        - This method is called from start() defined in social network manager
            inside social_network_service/manager.py.

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.process('event', user_credentials=user_credentials)

        **See Also**
        .. seealso:: start() function defined in social network manager
            inside social_network_service/manager.py.
        """
        user_id = self.user.id
        social_network_id = self.social_network.id
        social_network_name = self.social_network.name
        try:
            sn_name = self.social_network.name.strip()
            # get_required class under social_network_service/event/ to process events
            event_class = get_class(sn_name, 'event')
            # create object of selected event class
            sn_event_obj = event_class(user_credentials=user_credentials, social_network=self.social_network,
                                       headers=self.headers, **kwargs)
            if mode == EVENT:
                # gets events using respective API of Social Network
                logger.info('Getting event(s) of %s(UserId:%s) from %s website.' % (self.user.name, self.user.id,
                                                                                    self.social_network.name))
                self.events = sn_event_obj.get_events()
                logger.info('Got %s live event(s) of %s(UserId: %s) on %s within provided time range.'
                             % (len(self.events), self.user.name, self.user.id, self.social_network.name))
                # process events to save in database
                sn_event_obj.process_events(self.events)
            elif mode == RSVP:
                sn_event_obj.process_events_rsvps(user_credentials, headers=self.headers,
                                                  social_network=self.social_network)
        except Exception:
            logger.exception('process: running %s importer, user_id: %s, social network: %s(id: %s)'
                             % (mode, user_id, social_network_name, social_network_id))

    @classmethod
    def get_access_and_refresh_token(cls, user_id, social_network, code_to_get_access_token=None, method_type=None,
                                     payload=None, params=None, api_relative_url=None):
        """
        This function is used by Social Network API to save 'access_token' and 'refresh_token' for specific
        social network against a user (current user) by sending an POST call to respective social network API.
        :param user_id: current user id
        :param social_network: social_network in getTalent database
        :param code_to_get_access_token: Code which is exchanged for an access token.
        :param method_type: In case of Eventbrite, need to make a 'POST' call to get access token.
        :param payload: is set inside this method and is passed in super constructor. This is sent in body
                        of HTTP request.
        :param params: dictionary of data to send in the url params.
        :param api_relative_url: This variable is set in this function and is passed in super constructor to make
                                HTTP request.
        :type user_id: int
        :type social_network: common.models.social_network.SocialNetwork
        :type code_to_get_access_token: str
        :type method_type: str
        :type payload: dict
        :type payload: dict
        :type api_relative_url: str
        :return: returns access token and refresh token
        :rtype: tuple (str, str)
        """
        logger.info('Getting "access_token and refresh_token" of user_id:%s using API of %s.'
                    % (user_id, social_network.name))
        url = social_network.auth_url + api_relative_url
        get_token_response = http_request(method_type, url, data=payload, user_id=user_id, params=params)
        try:
            if get_token_response.ok:
                # access token is used to make API calls, this is what we need
                # to make subsequent calls
                try:
                    response = get_token_response.json()
                    access_token = response.get('access_token')
                    # refresh token is used to refresh the access token
                    refresh_token = response.get('refresh_token')
                except ValueError:
                    if 'facebook' in social_network.api_url:
                        # In case of Facebook, access_token is retrieved as follows
                        access_token = \
                            get_token_response.content.split('=')[1].split('&')[0]
                        refresh_token = ''
                    else:
                        raise
                return access_token, refresh_token
            else:
                log_error({'user_id': user_id, 'error': get_token_response.json().get('error')})
                raise SNServerException('Unable to to get access token for current user')

        except:
            logger.exception('get_access_and_refresh_token: user_id: %s, social network: %s(id: %s)'
                             % (user_id, social_network.name, social_network.id))
            raise SNServerException('Unable to create user credentials for current user')

    def get_member_id(self):
        """
        - If getTalent user has an account on some social network, like Meetup.com, it will have a "member id" for
            that social network. This "member id" is used to make API subsequent calls to fetch events or RSVPs and
            relevant data for getTalent user from social network website.

        :Example:

            from social_network_service.meetup import Meetup
            sn = Meetup(user_id=1)
            sn.get_member_id()

        - We call this method from connect() of SocialNetworkBase class so that we don't need to get 'member id'
            of getTalent user while making object of some social network class at different places.
            (e.g. creating object of Meetup() in when importing events)

        **See Also**
        .. seealso:: connect() method defined in SocialNetworkBase class inside social_network_service/base.py.
        """
        logger.info('Getting "member id" of %s(user id:%s) using API of %s.' % (self.user.name, self.user.id,
                                                                                self.social_network.name))
        url = get_url(self, SocialNetworkUrls.VALIDATE_TOKEN)
        # Now we have the URL, access token, and header is set too,
        response = http_request('POST', url, headers=self.headers, user_id=self.user.id, app=app)
        if response.ok:
            return response.json().get('id')
        else:
            logger.error('get_member_id: Error:%s.' % response.text)

    def validate_token(self, payload=None):
        """
        :param payload: contains the access token of Facebook (Child class
            sets the payload) or is None for other social networks.
        :type payload: dict
        :return: True if token is valid otherwise False
        :rtype: bool

        - This function is called from validate_and_refresh_access_token() social network service base class
        inside social_network_service/base.py to check the validity of the access token of current user for a
        specific social network. We take the access token, make request to social network API on url
            say for Meetup 'https://api.meetup.com/2/member/self'

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.validate_token()

        **See Also**
        .. seealso:: __init__() function defined in social network manager
            inside social_network_service/manager.py.

        :return status of of access token either True or False.
        """
        status = False
        url = get_url(self, SocialNetworkUrls.VALIDATE_TOKEN)
        logger.info("%s access_token validation url: %s", self.social_network.name, url)
        try:
            response = requests.get(url, headers=self.headers, params=payload)
            if response.ok:
                status = True
            # If hit rate limit reached for Eventbrite or Meetup, too many requests
            elif response.status_code == codes.TOO_MANY_REQUESTS:
                data = response.json()
                logger.error("HitLimit reached for user(id:%s). Error:%s" % (self.user.id, data))
                raise HitLimitReached(data)
            else:
                logger.info("Access token has expired for %s(UserId:%s). Social Network is %s."
                            % (self.user.name, self.user.id, self.social_network.name))
        except requests.RequestException as error:
            raise AccessTokenHasExpired('Error: %s, Please connect with %s again from "Profile" page.'
                                        % (error.message, self.social_network.name))
        return status

    def refresh_access_token(self):
        """
        - This function is used to refresh the access token. Child class
            will implement this if needed (e.g. meetup for now).

        - This function is called from validate_and_refresh_access_token()
            defined SocialNetworkBase inside social_network_service/base.py

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.refresh_access_token()

        **See Also**
        .. seealso:: refresh_access_token() method defined in Meetup class
            inside social_network_service/meetup.py.

        .. seealso:: validate_and_refresh_token() method defined in
            SocialNetworkBase class inside social_network_service/base.py.

        :return True if token has been refreshed successfully, False otherwise.
        :rtype: bool

        """
        return False

    def validate_and_refresh_access_token(self):
        """
        - This validates the access token. If access token has
        expired, it also refreshes it and saves the fresh access token in
         database.

        - It calls validate_access_token() and refresh_access_token() defined
            in SocialNetworkBase class inside social_network_service/base.py

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.validate_and_refresh_access_token()

        **See Also**
        .. seealso:: __init__() method of SocialNetworkBase class
            inside social_network_service/base.py.

        :return the True if token has been refreshed, False otherwise.
        :rtype: bool
        """
        access_token_status = self.validate_token()
        if not access_token_status:
            # access token has expired, need to refresh it
            return self.refresh_access_token()
        return access_token_status

    @classmethod
    def save_user_credentials_in_db(cls, user_credentials):
        """
        :param user_credentials: user's social network credentials
        :type user_credentials: dict

        - It checks if user_credentials are already in database. If a record
            is found, it updates the record otherwise it saves as new record.

        - It is called e.g. from refresh_access_token() inside
            social_network_service/meetup.py

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.save_user_credentials_in_db(data)

        **See Also**
        .. seealso:: refresh_access_token() method of Meetup class
            inside social_network_service/meetup.py

        :return user's social network credentials
        :rtype: common.models.user.UserCredentials
        """
        user_credentials_in_db = UserSocialNetworkCredential.get_by_user_and_social_network_id(
            user_credentials['user_id'], user_credentials['social_network_id'])
        try:
            if user_credentials_in_db:
                user_credentials_in_db.update(**user_credentials)
            else:
                user_credentials_in_db = UserSocialNetworkCredential(**user_credentials)
                UserSocialNetworkCredential.save(user_credentials_in_db)
            return user_credentials_in_db
        except:
            logger.exception('save_user_credentials_in_db: user_id: %s',
                             user_credentials['user_id'])
            raise SNServerException('APIError: Unable to create user credentials')

    @staticmethod
    def save_venue(venue_data):
        """
        This function will take dictionary data and will save it in database as Venue reccord.
        :param dict venue_data: venue data
        """
        valid_fields = ['address_line_1', 'address_line_2', 'city', 'country', 'latitude', 'longitude',
                        'zip_code', 'user_id', 'social_network_id', 'social_network_venue_id']
        venue_data = {key: venue_data[key] for key in venue_data if key in valid_fields}
        required_fields = ['social_network_id', 'user_id']
        for key in required_fields:
            if key not in venue_data:
                raise InvalidUsage('Required field missing in venue data. Field: %s' % key)
        venue = Venue(**venue_data)
        Venue.save(venue)
        return venue

    def connect(self, code):
        """
        This connects user with social-network's account. e.g. on Meetup or Eventbrite etc.
        This gets access token and refresh tokens for user and it also updates these tokens for previously connected
        users. It also gets member_id of getTalent user for requested social-network website.
        :param string code: code to exchange for access token and refresh token.
        """
        access_token, refresh_token = self.get_access_and_refresh_token(self.user.id, self.social_network,
                                                                        code_to_get_access_token=code)
        self.headers = {'Authorization': 'Bearer ' + access_token}
        # GET member_id of getTalent user
        member_id = self.get_member_id()
        if not member_id:
            raise InternalServerError('Could not get member id from social-network:%s' % self.social_network.name)
        # Check all user_social_network_credentials in database against this member_id
        records_in_db = UserSocialNetworkCredential.filter_by_keywords(social_network_id=self.social_network.id,
                                                                       member_id=member_id)
        user_credentials_dict = dict(user_id=self.user.id, social_network_id=self.social_network.id,
                                     access_token=access_token, refresh_token=refresh_token, member_id=member_id)

        if not records_in_db:  # No record found in database
            return self.save_user_credentials_in_db(user_credentials_dict)

        if len(records_in_db) >= 1:
            for record in records_in_db:
                if record.user.domain_id == self.user.domain_id:
                    error_message = 'Some other user is already using this account. user_id:%s, social_network:%s , ' \
                                    'member_id:%s.' % (self.user.id, self.social_network.name.title(), member_id)
                    logger.error(error_message)
                    raise InvalidUsage(error_message)
                elif record.user.id == self.user.id:
                    error_message = 'You are already connected to this account.'
                    logger.error(error_message)
                    raise InvalidUsage(error_message)
                else:
                    # updating new  access and refresh tokens for all user connected with same meetup account.
                    record.access_token = access_token
                    record.refresh_token = refresh_token

            db.session.commit()
            return self.save_user_credentials_in_db(user_credentials_dict)

    @classmethod
    def disconnect(cls, user_id, social_network):
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(user_id, social_network.id)
        if user_credentials:
            UserSocialNetworkCredential.delete(user_credentials)
        return user_credentials
