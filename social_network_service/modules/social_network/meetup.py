"""
This modules contains Meetup class. It inherits from SocialNetworkBase
class. Meetup contains methods like refresh_access_token(), get_groups() etc.
"""

# Standard Library
import json
import time

# 3rd party imports
from requests import codes

# Application Specific
from social_network_service.common.models.event import MeetupGroup
from social_network_service.common.models.db import db
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.models.venue import Venue
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.common.error_handling import InternalServerError, InvalidUsage, ForbiddenError
from social_network_service.modules import custom_codes
from social_network_service.modules.constants import MEETUP_VENUE
from social_network_service.modules.custom_codes import (VENUE_EXISTS_IN_GT_DATABASE,
                                                         INVALID_MEETUP_RESPONSE, MEETUP_ACCOUNT_ALREADY_EXISTS)
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls
from social_network_service.modules.urls import get_url
from social_network_service.modules.utilities import logger
from base import SocialNetworkBase
from social_network_service.social_network_app import app


class Meetup(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.

    - This overrides following SocialNetworkBase class methods

        - validate_token()
        - get_access_and_refresh_token()

    - It also defines
        - refresh_access_token() to refresh the access token
        - get_groups() to get the groups from Meetup API for which the
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

    def get_groups(self):
        """
        - This function fetches the groups of user from Meetup website for
            which the user is an organizer. These groups are shown
            in drop down while creating event on Meetup through Event Creation
            Form.

        - This function is called from GET method of class MeetupGroups() inside
            social_network_service/app/restful/social_network.py

        :Example:
                from social_network_service.meetup import Meetup
                sn = Meetup(user_id=1)
                sn.get_groups()
        :return: Meetup groups for which gt-user is an organizer
        :rtype: list (list of dicts where each dict is likely the response from
                    Meetup API)
        **See Also**
        .. seealso:: GET method of class MeetupGroups() inside
            social_network_service/app/restful/social_network.py
        """
        url = get_url(self, SocialNetworkUrls.GROUPS)
        params = {'organizer_id': self.user_credentials.member_id}
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('GET', url, params=params, headers=self.headers, user_id=self.user.id)
        if response.ok:
            return response.json()['results']
        else:
            return []

    def import_meetup_groups(self):
        """
        This method is to fetch user's meetup groups and save them in gt database.
        """
        url = get_url(self, SocialNetworkUrls.GROUPS)
        params = {'organizer_id': self.user_credentials.member_id}
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('GET', url, params=params, headers=self.headers, user_id=self.user.id)
        meetup_groups = []
        if response.ok:
            groups = response.json()['results']
            for group in groups:
                meetup_group = MeetupGroup.get_by_group_id(group['id'])

                if meetup_group:
                    if meetup_group.user_id == self.user.id:
                        meetup_groups.append(meetup_group.to_json())
                        continue
                meetup_group = MeetupGroup(
                    group_id=group['id'],
                    user_id=self.user.id,
                    name=group['name'],
                    url_name=group['urlname'],
                    description=group.get('description'),
                    created_datetime=group.get('created'),
                    visibility=group.get('visibility'),
                    country=group.get('country'),
                    state=group.get('state'),
                    city=group.get('city'),
                    timezone=group.get('timezone')
                )
                MeetupGroup.save(meetup_group)
                meetup_groups.append(meetup_group.to_json())
        return meetup_groups

    def refresh_access_token(self):
        """
        - When user authorizes Meetup account, we get a refresh token
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
        :rtype: bool
        """
        status = False
        user_refresh_token = self.user_credentials.refresh_token

        auth_url = get_url(self, SocialNetworkUrls.REFRESH_TOKEN, is_auth=True)
        client_id = self.social_network.client_key
        client_secret = self.social_network.secret_key

        payload_data = {'client_id': client_id,
                        'client_secret': client_secret,
                        'grant_type': u'refresh_token',
                        'refresh_token': user_refresh_token}
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('POST', url=auth_url, data=payload_data,
                                user_id=self.user.id, app=app)
        if response.ok:
            try:
                # access token has been refreshed successfully, need to update
                # self.access_token and self.headers
                response = response.json()
                self.access_token = response.get('access_token')
                self.headers.update({'Authorization': 'Bearer ' + self.access_token})
                refresh_token = response.get('refresh_token')
                UserSocialNetworkCredential.query.filter_by(social_network_id=self.social_network.id,
                                                            member_id=self.user_credentials.member_id).\
                    update({'access_token': self.access_token, 'refresh_token': refresh_token})
                db.session.commit()
                logger.info("Access token has been refreshed.")
                status = True
            except Exception:
                logger.exception('refresh_access_token: user_id: %s' % self.user.id)
        else:
            # Error has been logged inside http_request()
            pass
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
        :param social_network: social_network in getTalent database.
        :param code_to_get_access_token: Code which is exchanged for an
                access token.
        :param method_type: In case of Meetup, need to make a 'POST' call
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
        api_relative_url = "/access"
        # create Social Network Specific payload data
        payload_data = {'client_id': social_network.client_key,
                        'client_secret': social_network.secret_key,
                        'grant_type': 'authorization_code',
                        'redirect_uri': social_network.redirect_uri,
                        'code': code_to_get_access_token}
        # calls super class method with api_relative_url and payload data
        return super(Meetup, cls).get_access_and_refresh_token(
            user_id, social_network, method_type=method_type, payload=payload_data,
            api_relative_url=api_relative_url)

    def add_venue_to_sn(self, venue_data):
        """
        This function sends a POST request to Meetup api to create a venue for event.
        :param dict venue_data: a dictionary containing data required to create a venue
        """
        if not venue_data.get('group_url_name'):
            raise InvalidUsage("Mandatory Input Missing: group_url_name",
                               error_code=custom_codes.MISSING_REQUIRED_FIELDS)
        url = get_url(self, SocialNetworkUrls.VENUES, custom_url=MEETUP_VENUE).format(
            venue_data['group_url_name'])
        payload = {
            'address_1': venue_data['address_line_1'],
            'address_2': venue_data.get('address_line_2'),
            'city': venue_data['city'],
            'country': venue_data['country'],
            'state': venue_data['state'],
            'name': venue_data['address_line_1']
        }
        # Sleep for 10 / 30 seconds to avoid throttling
        time.sleep(0.34)
        response = http_request('POST', url, params=payload,
                                headers=self.headers,
                                user_id=self.user.id)
        json_resp = response.json()
        if response.ok:
            venue_id = json_resp['id']
            logger.info('Venue has been Added. Venue Id: %s', venue_id)
        elif response.status_code == codes.CONFLICT:
            # 409 is returned when our venue is matching existing
            # venue/venues.
            try:
                match_id = json_resp['errors'][0]['potential_matches'][0]['id']
            except:
                raise InternalServerError('Invalid response from Meetup', error_code=INVALID_MEETUP_RESPONSE)
            venue = Venue.get_by_user_id_and_social_network_venue_id(self.user.id, match_id)
            if venue:
                raise InvalidUsage('Venue already exists in getTalent database', additional_error_info=dict(id=venue.id),
                                   error_code=VENUE_EXISTS_IN_GT_DATABASE)
            venue_id = json_resp['errors'][0]['potential_matches'][0]['id']
        else:
            raise InternalServerError('ApiError: Unable to create venue for Meetup',
                                      additional_error_info=dict(venue_error=json_resp))

        venue_data['user_id'] = self.user.id
        venue_data['social_network_venue_id'] = venue_id
        return SocialNetworkBase.save_venue(venue_data)

    @classmethod
    def save_user_credentials_in_db(cls, user_credentials):
        """
        :param user_credentials: User's social network credentials for Meetup.
        :type user_credentials: dict
        - This overrides the SocialNetworkBase class method
            save_user_credentials_in_db() because in case of user credentials
            related to Eventbrite, we also need to create webhook.
        - It first saves the credentials in db, gets the Meetup Groups by calling
            import_meetup_groups()using Meetup's API and updates the record in db.
        **See Also**
        .. seealso:: save_user_credentials_in_db() function defined in
            SocialNetworkBase class inside social_network_service/base.py.
        .. seealso::POST method of end point ProcessAccessToken()
            defined in social network Rest API inside
            social_network_service/app/restful/social_network.py.
        """
        user_credentials_in_db = super(cls, cls).save_user_credentials_in_db(user_credentials)
        try:
            meetup = cls(user_id=user_credentials_in_db.user_id,
                         social_network_id=user_credentials_in_db.social_network_id)
            meetup.import_meetup_groups()
        except Exception as e:
            UserSocialNetworkCredential.delete(user_credentials_in_db)
            raise
        return user_credentials_in_db

    @classmethod
    def disconnect(cls, user_id, social_network):
        """
        Delete user credentials for Meetup and delete all MeetupGroup from db that belong to this user.
        :param int | long user_id: user id
        :param int | long social_network: social network model object
        """
        MeetupGroup.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        MeetupGroup.session.commit()
        user_credentials = super(cls, cls).disconnect(user_id, social_network)
        return user_credentials
