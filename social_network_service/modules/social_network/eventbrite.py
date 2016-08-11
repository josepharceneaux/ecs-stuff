"""
This modules contains Eventbrite class. It inherits from SocialNetworkBase
class. Eventbrite contains methods like create_webhook(), get_member_id() etc.
"""

# 3rd party imports
import requests

# Application Specific
from base import SocialNetworkBase
from social_network_service.common.error_handling import InternalServerError, InvalidUsage
from social_network_service.common.utils.handy_functions import http_request, find_missing_items
from social_network_service.modules.custom_codes import ORGANIZER_ALREADY_EXISTS
from social_network_service.social_network_app import logger


class Eventbrite(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.

    - This overrides following SocialNetworkBase class methods

        1- get_member_id()
        2- validate_token()
        3- get_access_and_refresh_token()

    :Example:

        1- Get the user credentials first
            from social_network_service.common.models.user import UserSocialNetworkCredential
            user_credentials = UserSocialNetworkCredential.get_by_id(1)

        **See Also**
            .. seealso:: ProcessAccessToken() method in
            social_network_service/app/restful/social_network.py.
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
        url = self.api_url + "/venues/"
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
        missing_items = find_missing_items(data, mandatory_input_data, verify_all=True)
        if missing_items:
            raise InvalidUsage("Mandatory Input Missing: %s" % missing_items)

        payload = {
                'organizer.name': data['name'],
                'organizer.description.html': data['about']
            }
        # create url to send post request to create organizer
        url = "%s/organizers/" % self.api_url
        response = http_request('POST', url, params=payload,
                                headers=self.headers,
                                user_id=self.user.id)
        json_response = response.json()
        if response.ok:
            return json_response['id']
        elif response.status_code == requests.codes.BAD_REQUEST and json_response.get('error') == "NOT_ALLOWED":
            raise InvalidUsage('Organizer name already exists', error_code=ORGANIZER_ALREADY_EXISTS)
        raise InternalServerError('Error occurred while creating organizer.',
                                  additional_error_info=dict(error=json_response))

