"""
This modules contains Eventbrite class. It inherits from SocialNetworkBase
class. Eventbrite contains methods like create_webhook(), get_member_id() etc.
"""

# Application Specific
from base import SocialNetworkBase
from utilities import http_request
from social_network_service import flask_app as app, logger
from social_network_service.custom_exceptions import *

WEBHOOK_REDIRECT_URL = app.config['WEBHOOK_REDIRECT_URL']


class Eventbrite(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.

    - This overrides following SocialNetworkBase class methods

        1- get_member_id()
        2- validate_token()
        3- get_access_and_refresh_token()
        4- save_user_credentials_in_db()

    - It also defines following method
            1- create_webhook()
        to create webhook for getTalent user.

    :Example:

        - To create the webhook for getTalent user

        1- Get the user credentials first
            from social_network_service.common.models.user import UserSocialNetworkCredential
            user_credentials = UserSocialNetworkCredential.get_by_id(1)

        2. Call create_webhook() on class and pass user credentials in arguments
            Eventbrite.create_webhook(user_credentials)

        **See Also**
            .. seealso:: ProcessAccessToken() method in
            social_network_service/app/restful/social_network.py.

        .. note::
            You can learn more about webhook and Eventbrite API from following link
            - https://www.eventbrite.com/developer/v3/
    """

    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)

    def get_member_id(self):
        """
        - If getTalent user has an account on Eventbrite website, it will
            have a "member id" which is used to make API subsequent calls to
            fetch events or RSVPs and relevant data for getTalent user from
            social network website.

        - Here we set the value of "self.api_relative_url". We then call super
            class method get_member_id() to get the "member id".
            get_member_id() in SocialNetworkBase makes url like
                url = self.social_network.api_url + self.api_relative_url
            (This will evaluate in case of Eventbrite as
                url = 'https://www.eventbriteapi.com/v3' + '/users/me/')
            After this, it makes a POST call on this url and check if status
            of response is 2xx.

        - This method is called in __int__() of SocialNetworkBase class to
            get and save member_id in getTalent db table
            user_social_network_credential for a particular record.

        **See Also**
        .. seealso:: get_member_id() method defined in SocialNetworkBase
            class inside social_network_service/base.py.

        .. seealso:: __init__() method of SocialNetworkBase class.
        """
        self.api_relative_url = "/users/me/"
        super(Eventbrite, self).get_member_id()

    def validate_token(self, payload=None):
        """
        :param payload is None in case of Eventbrite as we pass access token
            in headers:
        :return: True if access token is valid otherwise False
        :rtype: bool
        - Here we set the value of "self.api_relative_url". We then call super
            class method validate_token() to validate the access token.
            validate_token() in SocialNetworkBase makes url like
                url = self.social_network.api_url + self.api_relative_url
            (This will evaluate in case of Eventbrite as
                url = 'https://www.eventbriteapi.com/v3' + '/users/me/')
            After this, it makes a POST call on this url and check if status
            of response is 2xx.

        - This method is called from validate_and_refresh_access_token()
            defined in SocialNetworkBase class inside
            social_network_service/base.py.

        **See Also**
        .. seealso:: validate_token() function defined in SocialNetworkBase
            class inside social_network_service/base.py.
        """
        self.api_relative_url = '/users/me/'
        return super(Eventbrite, self).validate_token()

    @staticmethod
    def save_user_credentials_in_db(user_credentials):
        """
        :param user_credentials: User's social network credentials for which
                we need to create webhook. Webhook is created to be updated
                about any RSVP on an event of Eventbrite.
        :type user_credentials: dict

        - This overrides the SocialNetworkBase class method
            save_user_credentials_in_db() because in case of user credentials
            related to Eventbrite, we also need to create webhook.

        - It first saves the credentials in db, gets the webhook id by calling
            create_webhook()using Eventbrite's API and updates the record in db.

        - This method is called from POST method of end point ProcessAccessToken()
            defined in social network Rest API inside
            social_network_service/app/restful/social_network.py.

        **See Also**
        .. seealso:: save_user_credentials_in_db() function defined in
            SocialNetworkBase class inside social_network_service/base.py.

        .. seealso::POST method of end point ProcessAccessToken()
            defined in social network Rest API inside
            social_network_service/app/restful/social_network.py.
        """
        user_credentials_in_db = super(Eventbrite,
                                       Eventbrite).save_user_credentials_in_db(user_credentials)
        Eventbrite.create_webhook(user_credentials_in_db)

    @classmethod
    def get_access_and_refresh_token(cls, user_id, social_network,
                                     code_to_get_access_token=None,
                                     method_type='POST',
                                     payload=None,
                                     params=None,
                                     api_relative_url=None):
        """
        - This function is used by Social Network API to get
            'access_token' for Eventbrite social network against a user (current
            user) by using code_to_get_access_token by sending a POST call to
            Eventbrite API.

        - Here we set the payload data to pass in HTTP request for exchange of
            access token.

        - Once access_token is saved in db, we create webhook for user and
            update user credentials in db.

        :param user_id: current user id.
        :param social_network: social_network in getTalent database.
        :param code_to_get_access_token: Code which is exchanged for an
                access token.
        :param method_type: In case of Eventbrite, need to make a 'POST' call
                to get access token.
        :param payload: is set inside this method and is passed in super
                constructor. This is sent in body of HTTP request.
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
        api_relative_url = "/token"
        # create Social Network Specific payload data
        payload_data = {'client_id': social_network.client_key,
                        'client_secret': social_network.secret_key,
                        'grant_type': 'authorization_code',
                        'redirect_uri': social_network.redirect_uri,
                        'code': code_to_get_access_token}
        # calls super class method with api_relative_url and payload data
        return super(Eventbrite, cls).get_access_and_refresh_token(
            user_id, social_network, method_type=method_type, payload=payload_data,
            api_relative_url=api_relative_url)

    @classmethod
    def create_webhook(cls, user_credentials):
        """
        :param user_credentials: User's social network credentials for which
                we need to create webhook. Webhook is created to be updated
                about any RSVP on an
                event of Eventbrite.
        :type user_credentials:  common.models.user.UserSocialNetworkCredential

        - This method creates a webhook to stream the live feed of RSVPs of
            Eventbrite events to the getTalent app. Once we have the webhook
            id for given user, we update user credentials in db.

        - It also performs a check which ensures that webhook is not generated
            every time code passes through this flow once a webhook has been
            created for a user (since webhook don't expire and are unique for
            every user).

        - This method is called from save_user_credentials_in_db() defined in
            Eventbrite class inside social_network_service/eventbrite.py.

        **See Also**
        .. seealso:: save_user_credentials_in_db() function defined in Eventbrite
            class inside social_network_service/eventbrite.py.

        .. seealso:: get_access_and_refresh_token() function defined in Eventbrite
            class inside social_network_service/eventbrite.py.
        """
        url = user_credentials.social_network.api_url + "/webhooks/"
        payload = {'endpoint_url': WEBHOOK_REDIRECT_URL}
        headers = {'Authorization': 'Bearer ' + user_credentials.access_token}
        response = http_request('POST', url, params=payload, headers=headers,
                                user_id=user_credentials.user.id)
        try:
            webhook_id = response.json()['id']
            user_credentials.update(webhook=webhook_id)
        except:
            logger.exception('create_webhook: user_id: %s' % user_credentials.user.id)
            raise SocialNetworkApiException("Eventbrite Webhook wasn't created successfully")
