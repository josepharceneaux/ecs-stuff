"""
This modules contains Facebook class. It inherits from SocialNetworkBase
class. Facebook contains method validate_token() for now.
"""

# Application Specific
from social_network_service.base import SocialNetworkBase


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
                                     code_to_get_extended_token=None,
                                     method_type='GET',
                                     payload=None,
                                     api_relative_url=None):
        """
        - This function is used by Social Network API to get extended
            'access_token' for Facebook social network against a user (current
            user) by using code_to_get_extended_token by sending a GET call to
            Facebook API.

        - Here we set the payload data to pass in HTTP request for exchange of
            access token.

        :param user_id: current user id
        :type user_id: int
        :param social_network: social_network in getTalent database
        :type social_network: common.models.social_network.SocialNetwork
        :param code_to_get_extended_token: Code which is exchanged for an
                access token
        :param method_type: In case of Facebook, need to make a GET call.
        :param payload: is set inside this method and is passed in super
                constructor.
        :type payload: dict
        :param api_relative_url: This variable is set in this function and
                is passed in super constructor to make HTTP request.
        """
        api_relative_url = "/access_token"
        # create Social Network Specific payload data
        payload_data = {'client_id': social_network.clientKey,
                        'client_secret': social_network.secretKey,
                        'grant_type': 'fb_exchange_token',
                        'fb_exchange_token': code_to_get_extended_token,
                        'redirect_uri': social_network.redirectUri}
        # calls super class method with api_relative_url and payload data
        super(Facebook, cls).get_access_and_refresh_token(
            user_id, social_network, method_type=method_type, payload=payload_data,
            api_relative_url=api_relative_url)

    def validate_token(self, payload=None):
        """
        :param payload: payload is set here which contains the access token.

        - We also  set the API relative url and put it in
            "self.api_relative_url".

        - We then call super class method validate_token() to validate the
            access token.

        - This method is called from validate_and_refresh_access_token() defined in
            socialNetworkBase class inside social_network_service/base.py.

        **See Also**
        .. seealso:: validate_token() function defined in socialNetworkBase
            class inside social_network_service/base.py.
            """
        self.api_relative_url = '/me'
        payload = {'access_token': self.access_token}
        return super(Facebook, self).validate_token(payload=payload)
