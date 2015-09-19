from abc import ABCMeta, abstractmethod
import requests

from SocialNetworkService.utilities import get_message_to_log, log_error,\
    log_exception, http_request
from common.gt_models.social_network import SocialNetwork
from common.gt_models.user import User, UserCredentials


class SocialNetworkBase(object):
    __metaclass__ = ABCMeta

    def __init__(self,  *args, **kwargs):
        """
        This is a social network base class.
        This sets the user's credentials as base class property so that it
        can be used in other classes.
        :param args:
        :param kwargs:
        :return:
        """
        function_name = '__init__()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__)
        user_id = kwargs['user_id']
        social_network_id = kwargs['social_network_id']
        self.api_relative_url = None
        self.user = User.get_by_id(user_id)
        self.social_network = SocialNetwork.get_by_id(social_network_id)

        self.user_credentials = UserCredentials.get_by_user_and_social_network_id(
            user_id, social_network_id)

        if self.user_credentials:
            data = {
                "access_token": self.user_credentials.accessToken,
                "member_id": self.user_credentials.memberId,
                "gt_user_id": self.user_credentials.userId,
                "social_network_id": social_network_id,
                "api_url": self.social_network.apiUrl
            }
            # checks if any field is missing for given user credentials
            items = [value for key, value in data.iteritems() if key is not "api_url"]
            if all(items):
                self.api_url = data['api_url']
                self.member_id = data['member_id']
                self.gt_user_id = data['gt_user_id']
                self.social_network_id = data['social_network_id']
                self.access_token = data['access_token']
                self.headers = {'Authorization': 'Bearer ' + self.access_token}
            else:
                # gets fields which are missing
                items = [key for key, value in data.iteritems()
                         if key is not "api_url" and not value]
                missing_items = dict(missing_items=items)
                # Log those fields in error which are not present in Database
                error_message = "Missing Item(s) in user's credential: " \
                                "%(missing_items)s\n" % missing_items
                message_to_log.update({'error': error_message})
                log_error(message_to_log)
        else:
            error_message = 'User Credentials are None'
            message_to_log.update({'error': error_message})
            log_error(message_to_log)
        # Eventbrite and meetup social networks take access token in header
        # so here we generate authorization header to be used by both of them
        self.headers = {'Authorization': 'Bearer ' + self.access_token}
        self.message_to_log = get_message_to_log()

    @classmethod
    def get_access_token(cls, data):  # data contains social_network,
                                    # code to get access token, api_relative_url
        """
        This function is called from process_access_token() inside controller
        user.py. Here we get the access token from provided user_credentials
        and auth code for fetching access token by making API call.

        :return:
        """
        function_name = 'get_access_token()'
        message_to_log = get_message_to_log(function_name=function_name)
        access_token = None
        refresh_token = None
        auth_url = data['social_network'].authUrl + data['relative_url']
        payload_data = {'client_id': data['social_network'].clientKey,
                        'client_secret': data['social_network'].secretKey,
                        'grant_type': 'authorization_code',
                        'redirect_uri': data['social_network'].redirectUri,
                        'code': data['code']}
        get_token_response = http_request('POST', auth_url, data=payload_data,
                                          message_to_log=message_to_log)
        try:
            if get_token_response.ok:
                # access token is used to make API calls, this is what we need
                # to make subsequent calls
                response = get_token_response.json()
                access_token = response.get('access_token')
                # refresh token is used to refresh the access token
                refresh_token = response.get('refresh_token')
            else:
                error_message = get_token_response.json().get('error')
                message_to_log.update({'error': error_message})
                log_error(message_to_log)
        except Exception as e:
            error_message = e.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
        return access_token, refresh_token

    # Todo Need to update
    def get_member_id(self):
        """
        Once we have the access_token, we make API call on respective
        social network to get member id of user on that social network.
        :return:
        """
        function_name = 'get_member_id()'
        message_to_log = get_message_to_log(function_name=function_name)
        member_id = None
        url = self.api_url + self.api_relative_url
        # Now we have the URL, access token, and header is set too,
        get_member_id_response = http_request('POST', url, headers=self.headers,
                                              message_to_log=message_to_log)
        try:
            if get_member_id_response.ok:
                member_id = get_member_id_response.json().get('id')
        except Exception as e:
            error_message = e.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
        return member_id

    def validate_token(self, payload=None):
        """
        This function is called from get_and_update_auth_info() inside RESTful
        service social_networks() to check the validity of the access token
        of current user for a specific social network. We take the access token,
        make request to social network, and check if it didn't error'ed out.
        :param payload
        :return:
        """
        function_name = 'validate_token()'
        self.message_to_log.update({'function_name': function_name})
        status = False
        relative_url = self.api_relative_url
        url = self.api_url + relative_url
        try:
            response = requests.get(url, headers=self.headers, params=payload)
            if response.ok:
                status = True
            else:
                error_message = "Access token has expired for %s" % self.social_network.name
                self.message_to_log.update({'error': error_message})
                log_error(self.message_to_log)
        except requests.RequestException as e:
            error_message = e.message
            self.message_to_log.update({'error': error_message})
            log_exception(self.message_to_log)
        return status

    def refresh_access_token(self):
        """
        When user authorize to Meetup account, we get a refresh token
        and access token. Access token expires in one hour.
        Here we refresh the access_token using refresh_token without user
        :return:
        """
        return False

    def validate_and_refresh_access_token(self):
        """
        This function is called to validate access token. if access token has
        expired, it also refreshes it and saves the fresh access token in database
        :return:
        """
        refreshed_token_status = False
        access_token_status = self.validate_token()
        if not access_token_status:  # access token has expired, need to refresh it
            refreshed_token_status = self.refresh_access_token()
        return access_token_status, refreshed_token_status

    @staticmethod
    def save_token_in_db(user_credentials):
        """
        It puts the access token against the clicked social_network and and the
        logged in user of GT. It also calls create_webhook() class method of
        Eventbrite to create webhook for user.
        :return:
        """
        function_name = 'save_token_in_db()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            gt_user_id=user_credentials['userId'])
        gt_user_in_db = UserCredentials.get_by_user_and_social_network_id(
            user_credentials['userId'], user_credentials['socialNetworkId'])
        try:
            if gt_user_in_db:
                gt_user_in_db.update(**user_credentials)
            else:
                UserCredentials.save(**user_credentials)
        except Exception as e:
            error_message = e.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)

    def process_event(self):
        pass
