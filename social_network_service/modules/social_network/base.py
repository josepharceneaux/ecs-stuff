"""
This module contains SocialNetworkBase class which provides common methods for
all social networks like get_access_and_refresh_token(), validate_access_token(),
refresh_access_token(), get_member_id() and save_user_credentials_in_db() etc.
"""

# Standard Library
from abc import ABCMeta

# Third Party
import requests

# Application Specific
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.utilities import get_class
from social_network_service.modules.utilities import log_error
from social_network_service.common.models.user import User
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.social_network_app import logger
from social_network_service.modules.custom_exceptions import *


class SocialNetworkBase(object):
    """
    - This is the base class related to social networks. It contains the
        common functionality and some abstract methods which are implemented
        by child classes.

    - Currently we have the implementation for following social networks.

        1- Meetup
        2- Eventbrite
        3- Facebook

    - Usually API of any social network requires user permission to gain access
        of user's account. Once user allows access, we get an access token to
        play with the API of that social network. This access token expires in
        1- One hour (Meetup)
        2- Not expires until account password is changed (Eventbrite)
        3- Sixty days (Facebook).

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

    def __init__(self,  *args, **kwargs):
        """
        - This sets the user's credentials as base class property so that it
            can be used in other classes.

        - We also check the validity of access token and try to refresh it in
            case it has expired.
        :param args:
        :param kwargs:
        :return:
        """
        self.events = []
        self.api_relative_url = None
        user_id = kwargs.get('user_id')
        self.user = User.query.get(user_id)
        if isinstance(self.user, User):
            social_network = kwargs.get('social_network')
            if social_network and isinstance(social_network, SocialNetwork):
                self.social_network = social_network
            else:
                self.social_network = \
                    SocialNetwork.get_by_name(self.__class__.__name__)
            self.user_credentials = \
                UserSocialNetworkCredential.get_by_user_and_social_network_id(
                    user_id, self.social_network.id)
            if self.user_credentials:
                data = {
                    "access_token": self.user_credentials.access_token,
                    "gt_user_id": self.user_credentials.user_id,
                    "social_network_id": self.social_network.id,
                    "api_url": self.social_network.api_url,
                }
                # checks if any field is missing for given user credentials
                items = [value for key, value in data.iteritems()
                         if key is not "api_url"]
                if all(items):
                    self.api_url = data['api_url']
                    self.gt_user_id = data['gt_user_id']
                    self.social_network_id = data['social_network_id']
                    self.access_token = data['access_token']
                    self.headers = {
                        'Authorization': 'Bearer ' + self.access_token
                    }
                else:
                    # gets fields which are missing
                    items = [key for key, value in data.iteritems()
                             if key is not "api_url" and not value]
                    data_to_log = {'user_id': self.user.id,
                                   'missing_items': items}
                    # Log those fields in error which are not present in Database
                    error_message = \
                        "User id: %(user_id)s\n Missing Item(s) in user's " \
                        "credential: %(missing_items)s\n" % data_to_log
                    raise MissingFieldsInUserCredentials('API Error: %s'
                                                         % error_message)
            else:
                raise UserCredentialsNotFound('UserSocialNetworkCredential for social network '
                                              '%s and User Id %s not found in db.'
                                              % (self.__class__.__name__,
                                                 self.user.id))
        else:
            error_message = "No User found in database with id %(user_id)s" \
                            % kwargs.get('user_id')
            raise NoUserFound('API Error: %s' % error_message)
        # Eventbrite and meetup social networks take access token in header
        # so here we generate authorization header to be used by both of them
        self.headers = {'Authorization': 'Bearer ' + self.access_token}
        # token validity is checked here. If token is expired, we refresh it
        # here and save new access token in database.
        self.access_token_status = self.validate_and_refresh_access_token()
        if not self.access_token_status:
            # Access token has expired. Couldn't refresh it for given
            # social network.
            logger.debug('__init__: Access token has expired. '
                         'Please connect with %s again from "Profile" page. user_id: %s'
                         % (self.user.id, self.social_network.name))
            raise AccessTokenHasExpired('Access token has expired for %s' % self.social_network.name)
        self.start_date_dt = None
        self.webhook_id = None
        if not self.user_credentials.member_id:
            # gets and save the member id of gt-user
            self.get_member_id()

    def process(self, mode, user_credentials=None, rsvp_data=None):
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
        try:
            sn_name = self.social_network.name.strip()
            # get_required class under social_network_service/event/ to
            # process events
            event_class = get_class(sn_name, 'event')
            # create object of selected event class
            sn_event_obj = event_class(user_credentials=user_credentials,
                                       social_network=self.social_network,
                                       headers=self.headers)
            if mode == 'event':
                # gets events using respective API of Social Network
                logger.debug('Getting event(s) of %s(UserId: %s) from '
                             '%s website.' % (self.user.name, self.user.id,
                                              self.social_network.name))
                self.events = sn_event_obj.get_events()
                logger.debug('Got %s event(s) of %s(UserId: %s) on %s within '
                             'provided time range.'
                             % (len(self.events), self.user.name, self.user.id,
                                self.social_network.name))
                # process events to save in database
                sn_event_obj.process_events(self.events)
            elif mode == 'rsvp':
                sn_event_obj.process_events_rsvps(user_credentials,
                                                  rsvp_data=rsvp_data)
        except:
            logger.exception('process: running %s importer, user_id: %s, '
                             'social network: %s(id: %s)'
                             % (mode, self.user.id, self.social_network.name,
                                self.social_network.id))

    @classmethod
    def get_access_and_refresh_token(cls, user_id, social_network,
                                     code_to_get_access_token=None,
                                     method_type=None,
                                     payload=None,
                                     params=None,
                                     api_relative_url=None):
        """
        This function is used by Social Network API to save 'access_token'
        and 'refresh_token' for specific social network against a user (current
        user) by sending an POST call to respective social network API.
        :param user_id: current user id
        :param social_network: social_network in getTalent database
        :param payload: dictionary containing required data
                sample data
                payload_data = {'client_id': social_network.client_key,
                                'client_secret': social_network.secret_key,
                                'grant_type': 'authorization_code', # vendor
                                 specific
                                'redirect_uri': social_network.redirect_uri,
                                'code': code_to_get_access_token
                                }

        :type user_id: int
        :type social_network: common.models.social_network.SocialNetwork
        :type payload: dict
        :return: returns access token and refresh token
        :rtype: tuple (str, str)
        """
        url = social_network.auth_url + api_relative_url
        get_token_response = http_request(method_type, url, data=payload,
                                          user_id=user_id, params=params)
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
                log_error({'user_id': user_id,
                           'error': get_token_response.json().get('error')})
                raise SNServerException('Unable to to get access token for '
                                                'current user')

        except:
            logger.exception('get_access_and_refresh_token: user_id: %s, '
                             'social network: %s(id: %s)'
                             % (user_id, social_network.name, social_network.id))
            raise SNServerException('Unable to create user credentials for current'
                                            ' user')

    def get_member_id(self):
        """
        - If getTalent user has an account on some social network, like
            Meetup.com, it will have a "member id" for that social network.
            This "member id" is used to make API subsequent calls to fetch
            events or RSVPs and relevant data for getTalent user from social
            network website.

        ** Working **
            - In this method, we have value of "self.api_relative_url" set by
                child classes according to API of respective social network.
                "self.api_relative_url" is appended in "self.api_url" like
                    url = self.api_url + self.api_relative_url
                This will evaluate in case of Meetup as
                    url = 'https://api.meetup.com/2' + '/member/self'
                We then make a HTTP POST call on required url. If we
                get response status 2xx, we retrieve the "member id" from
                response of HTTP POST call and update the record in
                user_social_network_credentials db table.

        :Example:

            from social_network_service.meetup import Meetup
            sn = Meetup(user_id=1)
            sn.get_member_id()

        - We call this method from __init__() of SocialNetworkBase class so
            that we don't need to get 'member id' of getTalent user while
            making object of some social network class at different places.
            (e.g.
            1- creating object of Meetup() in start() method of manager.
            2- while processing event inside process_event() defined in
                social_network_service/utilities.py
            )

        **See Also**
        .. seealso:: __init__() method defined in SocialNetworkBase class
            inside social_network_service/base.py.
        """
        logger.debug('Getting "member id" of %s(user id: %s) using API of %s.'
                     % (self.user.name, self.user.id, self.social_network.name))
        try:
            user_credentials = self.user_credentials
            url = self.api_url + self.api_relative_url
            # Now we have the URL, access token, and header is set too,
            get_member_id_response = http_request('POST', url,
                                                  headers=self.headers,
                                                  user_id=self.user.id)
            if get_member_id_response.ok:
                member_id = get_member_id_response.json().get('id')
                data = dict(user_id=user_credentials.user_id,
                            social_network_id=user_credentials.social_network_id,
                            member_id=member_id)
                self.save_user_credentials_in_db(data)
            else:
                # Error has been logged inside http_request()
                pass
        except:
            logger.exception('get_member_id: user_id: %s, social network: %s(id: %s)'
                             % (self.user.id, self.social_network.name, self.social_network.id))

    def validate_token(self, payload=None):
        """
        :param payload: contains the access token of Facebook (Child class
            sets the payload) or is None for other social networks.
        :type payload: dict
        :return: True if token is valid otherwise False
        :rtype: bool

        - This function is called from validate_and_refresh_access_token()
         social network service base class inside
         social_network_service/base.py to check the validity of the access
         token of current user for a specific social network. We take the
         access token, make request to social network API on url
            url = self.api_url + self.api_relative_url
         and check if it didn't error out.

         We have value of "self.api_relative_url" set by child classes
            according to API of respective social network. Above url will
            evaluate in case of Meetup as
            url = 'https://api.meetup.com/2' + '/member/self'

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
        url = self.api_url + self.api_relative_url
        logger.info("Eventbrite url: %s" % url)
        try:
            response = requests.get(url, headers=self.headers, params=payload)
            if response.ok:
                status = True
            # If hit rate limit reached for eventbrite, too many requests
            elif response.status_code == 429:
                data = response.json()
                raise HitLimitReached('Error: %s, %s' %
                                      (data.get('error_description'), data.get('error')))
            else:
                logger.debug("Access token has expired for %s(UserId:%s)."
                             " Social Network is %s."
                             % (self.user.name, self.user.id,
                                self.social_network.name))
        except requests.RequestException as error:
            raise AccessTokenHasExpired('Error: %s, Please '
                                        'connect with %s again from "Profile" page.'
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

    @staticmethod
    def save_user_credentials_in_db(user_credentials):
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
                user_credentials = UserSocialNetworkCredential(**user_credentials)
                UserSocialNetworkCredential.save(user_credentials)
            return user_credentials_in_db
        except:
            logger.exception('save_user_credentials_in_db: user_id: %s',
                             user_credentials['user_id'])
            raise SNServerException('APIError: Unable to create user credentials')
