"""
This modules contains Facebook class. It inherits from SocialNetworkBase
class. Facebook contains method validate_token() for now.
"""

# Application Specific
from social_network_service.modules.social_networks.base import SocialNetworkBase


class Facebook(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.

    - This overrides following SocialNetworkBase class methods

        1- get_access_and_refresh_token()
        2- validate_token().

    :Example:

        - To validate access token of a user for Facebook

        1- Creates the object of this class by providing required parameters.
            from social_network_service.facebook import Facebook
            obj = Facebook(user_id=1)

        2. __init__() of Facebook simply calls super constructor.
            In __init__() of SocialNetworkBase class we call
            self.validate_and_refresh_access_token() which validates the
            access token and tries to refresh it.

        3. access token status can be check in
            obj.access_token_status

        **See Also**
            .. seealso:: validate_and_refresh_access_token() method in
            social_network_service/event/base.py for more insight.

        .. note::
            You can learn about Facebook API from following link
            - https://developers.facebook.com/docs/graph-api
    """

    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)

    @classmethod
    def get_access_and_refresh_token(cls, user_id, social_network,
                                     code_to_get_access_token=None,
                                     method_type='GET',
                                     payload=None,
                                     params=None,
                                     api_relative_url=None):
        """
        - This function is used by Social Network API to get extended
            'access_token' for Facebook social network against a user (current
            user) by using code_to_get_extended_token by sending a GET call to
            Facebook API.

        - Here we set the payload data to pass in HTTP request for exchange of
            access token.

        :param user_id: current user id.
        :param social_network: social_network in getTalent database.
        :param code_to_get_access_token: Code which is exchanged for an
                access token.
        :param method_type: In case of Facebook, we need to make a 'GET' call
                to get access token.
        :param payload: is set None for Facebook and data is sent in params.
        :param params: dictionary of data to send in the url params.
        :param api_relative_url: This variable is set in this function and
        is passed in super constructor to make HTTP request.

        :type user_id: int
        :type social_network: common.models.social_network.SocialNetwork
        :type code_to_get_access_token: str
        :type method_type: str
        :type payload: dict
        :type payload: dict
        :type api_relative_url: str
        :return: returns access token and refresh token
        :rtype: tuple
        """
        api_relative_url = "/access_token"
        # create Social Network Specific payload data
        payload_data = {'client_id': social_network.client_key,
                        'client_secret': social_network.secret_key,
                        'grant_type': 'fb_exchange_token',
                        'fb_exchange_token': code_to_get_access_token,
                        'redirect_uri': social_network.redirect_uri}
        # calls super class method with api_relative_url and payload data
        return super(Facebook, cls).get_access_and_refresh_token(
            user_id, social_network, method_type=method_type, params=payload_data,
            api_relative_url=api_relative_url)

    def validate_token(self, payload=None):
        """
        :param payload: payload is set here which contains the access token.
        :type payload: dict
        :return: True if access token is valid otherwise False
        :rtype: bool
        - Here we set the value of "self.api_relative_url". We then call super
            class method validate_token() to validate the access token.
            validate_token() in SocialNetworkBase makes url like
                url = self.social_network.api_url + self.api_relative_url
            (This will evaluate in case of Facebook as
                url = 'https://graph.facebook.com/v2.4' + '/me')
            After this, it makes a POST call on this url and check if status
            of response is 2xx.

        - This method is called from validate_and_refresh_access_token()
            defined in SocialNetworkBase class inside
            social_network_service/base.py.

        **See Also**
        .. seealso:: validate_token() function defined in SocialNetworkBase
            class inside social_network_service/base.py.
            """
        self.api_relative_url = '/me'
        payload = {'access_token': self.access_token}
        return super(Facebook, self).validate_token(payload=payload)
