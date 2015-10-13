"""
This modules contains Meetup class. It inherits from SocialNetworkBase
class. Meetup contains methods like refresh_access_token(), get_member_id() etc.
"""

# Standard Library
import json

# Application Specific
from utilities import logger
from utilities import log_error
from utilities import http_request
from utilities import log_exception
from base import SocialNetworkBase


class Meetup(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.

    - This overrides following SocialNetworkBase class methods

        1- get_member_id()
        2- validate_token()
        3- get_access_and_refresh_token()

    - It also defines
        1- refresh_access_token() to refresh the access token
        2- get_groups() to get the groups from Meetup API for which the
            getTalent user is an organizer.

    :Example:

        - To get the groups of getTalent user

        1- Creates the object of this class by providing required parameters.
            from social_network_service.meetup import Meetup
            obj = Meetup(user_id=1)

        2. Call get_groups on class object as
            groups = obj.get_groups()

        **See Also**
            .. seealso:: get_groups() method in
            social_network_service/meetup.py for more insight.

        .. note::
            You can learn about Meetup API from following link
            - https://secure.meetup.com/meetup_api/
    """
    def __init__(self, *args, **kwargs):
        super(Meetup, self).__init__(*args, **kwargs)

    def get_member_id(self):
        """
        - Here we set the API relative url and put it in
            "self.api_relative_url".

        - We then call super class method get_member_id() to get Id
            of user on Meetup website.

        - Member Id is used to fetch events or RSVPs of user from social
            network.

        - This method is called from start() defined in social network manager
            inside social_network_service/manager.py.

        **See Also**
        .. seealso:: get_member_id() function defined in socialNetworkBase
            class inside social_network_service/base.py.

        .. seealso:: start() function defined in social network manager
            inside social_network_service/manager.py.

        :return:
        """
        self.api_relative_url = '/member/self'
        super(Meetup, self).get_member_id()

    def get_groups(self):
        """
        - This function fetches the groups of user from Meetup website for
            which the user is an organizer. These groups are used to be shown
            in drop down while creating event on Meetup through Event Creation
            Form.

        - This function is called from GET method of class MeetupGroups() inside
            social_network_service/app/restful/social_network.py

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.get_groups()

        **See Also**
        .. seealso:: GET method of class MeetupGroups() inside
            social_network_service/app/restful/social_network.py
        """
        url = self.api_url + '/groups/'
        params = {'member_id': 'self'}
        response = http_request('GET', url, params=params,
                                headers=self.headers,
                                user_id=self.user.id)
        if response.ok:
            # If some error occurs during HTTP call,
            # we log it inside http_request()
            meta_data = json.loads(response.text)['meta']
            member_id = meta_data['url'].split('=')[1].split('&')[0]
            data = json.loads(response.text)['results']
            groups = filter(lambda item: item['organizer']['member_id']
                                         == int(member_id), data)
            return groups

    def validate_token(self, payload=None):
        """
        :param payload is None in case of Meetup as we pass access token
                    in headers:

        - Here we set the API relative url and put it in
            "self.api_relative_url".

        - We then call super class method validate_token() to validate the
            access token.

        - This method is called from validate_and_refresh_access_token() defined in
            socialNetworkBase class inside social_network_service/base.py.

        **See Also**
        .. seealso:: validate_token() function defined in socialNetworkBase
            class inside social_network_service/base.py.
        """
        self.api_relative_url = '/member/self'
        return super(Meetup, self).validate_token()

    def refresh_access_token(self):
        """
        - When user authorize to Meetup account, we get a refresh token
            and access token. Access token expires in one hour.
            Here we refresh the access_token using refresh_token without user
            involvement and save in user_credentials db table.


        - This function is called from validate_and_refresh_access_token()
            defined in SocialNetworkBase class inside
            social_network_service/base.py

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.refresh_access_token()

        **See Also**
        .. seealso:: validate_and_refresh_token() function defined in
            SocialNetworkBase class inside social_network_service/base.py.

        :return True if token has been refreshed successfully and False
                otherwise.
        """
        status = False
        user_refresh_token = self.user_credentials.refresh_token
        auth_url = self.social_network.auth_url + "/access?"
        client_id = self.social_network.client_key
        client_secret = self.social_network.secret_key
        payload_data = {'client_id': client_id,
                        'client_secret': client_secret,
                        'grant_type': 'refresh_token',
                        'refresh_token': user_refresh_token}
        response = http_request('POST', auth_url, data=payload_data,
                                user_id=self.user.id)
        try:
            if response.ok:
                # access token has been refreshed successfully, need to update
                # self.access_token and self.headers
                self.access_token = response.json().get('access_token')
                self.headers.update({'Authorization': 'Bearer ' + self.access_token})
                refresh_token = response.json().get('refresh_token')
                user_credentials_dict = dict(
                    user_id=self.user_credentials.user_id,
                    social_network_id=self.user_credentials.social_network_id,
                    access_token=self.access_token,
                    refresh_token=refresh_token,
                    member_id=self.user_credentials.member_id)
                status = self.save_user_credentials_in_db(user_credentials_dict)
                logger.debug("Access token has been refreshed for %s(UserId:%s)."
                             % (self.user.name, self.user.id))
            else:
                error_message = response.json().get('error')
                log_error({'user_id': self.user.id,
                           'error': error_message})
        except Exception as error:
            log_exception({'user_id': self.user.id,
                           'error': "Error occurred while refreshing access token. "
                                    "Error is: " + error.message})
        return status

    @classmethod
    def get_access_and_refresh_token(cls, user_id, social_network, code_to_get_access_token=None,
                                     method_type='POST',
                                     payload=None,
                                     params=None,
                                     api_relative_url=None):
        """
        - This function is used by Social Network API to get
            'access_token' for Meetup social network against a user (current
            user) by using code_to_get_access_token by sending a POST call to
            Meetup API.

        - Here we set the payload data to pass in HTTP request for exchange of
            access token.

        :param user_id: current user id.
        :type user_id: int.
        :param social_network: social_network in getTalent database.
        :type social_network: common.models.social_network.SocialNetwork.
        :param code_to_get_access_token: Code which is exchanged for an
                access token.
        :param method_type: In case of Meetup, need to make a POST call.
        :param payload: is set inside this method and is passed in super
                constructor.
        :type payload: dict.
        :param api_relative_url: This variable is set in this function and
                is passed in super constructor to make HTTP request.
        """
        api_relative_url = "/access"
        # create Social Network Specific payload data
        payload_data = {'client_id': social_network.client_key,
                        'client_secret': social_network.secret_key,
                        'grant_type': 'authorization_code',
                        'redirect_uri': social_network.redirect_uri,
                        'code': code_to_get_access_token}
        # calls super class method with api_relative_url and payload data
        super(Meetup, cls).get_access_and_refresh_token(
            user_id, social_network, method_type=method_type, payload=payload_data,
            api_relative_url=api_relative_url)

