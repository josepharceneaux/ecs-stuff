"""
This modules contains Eventbrite class. It inherits from SocialNetworkBase
class. Eventbrite contains methods like create_webhook(), get_access_and_refresh_token() etc.
"""

# 3rd party imports
import requests

# Application Specific
from base import SocialNetworkBase
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.modules.constants import ACTIONS
from social_network_service.modules.urls import get_url
from social_network_service.social_network_app import logger
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls as Urls
from social_network_service.modules.custom_codes import ORGANIZER_ALREADY_EXISTS
from social_network_service.common.error_handling import InternalServerError, InvalidUsage
from social_network_service.common.utils.handy_functions import http_request, find_missing_items


class Eventbrite(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.

    - This overrides following SocialNetworkBase class methods

        - get_access_and_refresh_token
        - save_user_credentials_in_db etc

    :Example:

        - Get the user credentials first
            from social_network_service.common.models.user import UserSocialNetworkCredential
            user_credentials = UserSocialNetworkCredential.get_by_id(1)

        **See Also**
            .. seealso:: ProcessAccessToken() method in
            social_network_service/app/restful/social_network.py.
    """

    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)

    @classmethod
    def save_user_credentials_in_db(cls, user_credentials):
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
        return user_credentials_in_db

    @classmethod
    def get_access_and_refresh_token(cls, user_id, social_network, code_to_get_access_token=None, method_type='POST',
                                     payload=None, params=None, api_relative_url=None):
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
        return super(Eventbrite, cls).get_access_and_refresh_token(user_id, social_network,
                                                                   method_type=method_type,
                                                                   payload=payload_data,
                                                                   api_relative_url=api_relative_url)

    def add_venue_to_sn(self, venue_data):
        """
        This function sends a POST request to Eventbrite api to create a venue for event.
        :param dict venue_data: a dictionary containing data required to create a venue
        """

        payload = {
            'venue.name': venue_data['address_line_1'],
            'venue.address.address_1': venue_data['address_line_1'],
            'venue.address.address_2': venue_data.get('address_line_2'),
            'venue.address.region': venue_data['state'],
            'venue.address.city': venue_data['city'],
            'venue.address.postal_code': venue_data.get('zip_code'),
            'venue.address.latitude': venue_data.get('latitude'),
            'venue.address.longitude': venue_data.get('longitude')
        }
        # create url to send post request to create venue
        url = get_url(self, Urls.VENUES)
        response = http_request('POST', url, params=payload,
                                headers=self.headers,
                                user_id=self.user.id)
        json_resp = response.json()
        if response.ok:
            logger.info('|  Venue has been created  |')
            venue_id = json_resp.get('id')
        else:
            raise InternalServerError('ApiError: Unable to create venue for Eventbrite',
                                      additional_error_info=dict(venue_error=json_resp))

        venue_data['user_id'] = self.user.id
        venue_data['social_network_venue_id'] = venue_id
        return SocialNetworkBase.save_venue(venue_data)

    def create_event_organizer(self, data):
        """
        This method sends a POST request to Eventbrite API to create an event organizer.
        :param dict[str, T] data: organizer data
        :return: organizer id on Eventbrite
        :rtype string
        """
        mandatory_input_data = ['name', 'about']
        # gets fields which are missing
        missing_items = find_missing_items(data, mandatory_input_data)
        if missing_items:
            raise InvalidUsage("Mandatory Input Missing: %s" % missing_items)

        payload = {
                'organizer.name': data['name'],
                'organizer.description.html': data['about']
            }
        # create url to send post request to create organizer
        url = get_url(self, Urls.ORGANIZERS)
        response = http_request('POST', url, params=payload,
                                headers=self.headers,
                                user_id=self.user.id)
        json_response = response.json()
        if response.ok:
            return json_response['id']
        elif response.status_code == requests.codes.BAD_REQUEST and json_response.get('error') == "ARGUMENTS_ERROR":
            raise InvalidUsage('Organizer name `{}` already exists on Eventbrite'.format(data['name']), error_code=ORGANIZER_ALREADY_EXISTS)
        raise InternalServerError('Error occurred while creating organizer.',
                                  additional_error_info=dict(error=json_response))

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
        cls.delete_webhooks(user_credentials)  # delete old webhooks
        payload = {'endpoint_url': SocialNetworkApiUrl.WEBHOOK % user_credentials.user_id,
                   'actions': ','.join([ACTIONS['published'],
                                        ACTIONS['unpublished'],
                                        ACTIONS['rsvp']])}
        headers = {'Authorization': 'Bearer ' + user_credentials.access_token}
        response = http_request('POST', url, params=payload, headers=headers,
                                user_id=user_credentials.user.id)
        try:
            webhook_id = response.json()['id']
            user_credentials.update(webhook=webhook_id)
        except Exception:
            logger.exception('create_webhook: user_id: %s' % user_credentials.user.id)
            raise InternalServerError("Eventbrite Webhook wasn't created successfully")

    @classmethod
    def delete_webhooks(cls, user_credentials):
        """
        This method deletes all webhooks for current user from eventbrite
        :param type(t) user_credentials: user credentials for eventbrite for this user
        """
        url = user_credentials.social_network.api_url + "/webhooks/"
        headers = {'Authorization': 'Bearer ' + user_credentials.access_token}
        response = http_request('GET', url, headers=headers,
                                user_id=user_credentials.user.id)
        if response.ok:
            webhooks = response.json()['webhooks']
            # Deleting all existing webhooks for this user because we don't know about their action types.
            # Need to register a webhook with `event.published` and `event.unpublished` actions and correct callback url
            for webhook in webhooks:
                http_request('DELETE', webhook['resource_uri'], headers=headers, user_id=user_credentials.user.id)

    @classmethod
    def disconnect(cls, user_id, social_network):
        """
        Delete user credentials for eventbrite and delete all webhooks for this user.
        :param int | long user_id: user id
        :param int | long social_network: social network model object
        """
        user_credentials = super(cls, cls).disconnect(user_id, social_network)
        if user_credentials:
            cls.delete_webhooks(user_credentials)
        return user_credentials
