import os
import json
from gt_common.models.config import GTSQLAlchemy
# app_cfg = os.path.abspath('app.cfg')
# logging_cfg = os.path.abspath('logging.conf')
#
# gt = GTSQLAlchemy(app_config_path=app_cfg,
#                   logging_config_path=logging_cfg)

from base import SocialNetworkBase
from utilities import http_request, logger, log_error, log_exception,\
    get_message_to_log


class Meetup(SocialNetworkBase):

    def __init__(self, *args, **kwargs):

        super(Meetup, self).__init__(*args, **kwargs)
        # token validity is checked here
        # if token is expired, we refresh it here
        self.validate_and_refresh_access_token()

    @classmethod
    def get_access_token(cls, data):
        """
        This function is called from process_access_token() inside controller
        user.py. Here we get the access token from provided user_credentials
        and auth code for fetching access token by making API call.
        :return:
        """
        data['api_relative_url'] = "/access"
        super(Meetup, cls).get_access_token(data)

    def get_member_id(self, data):
        """
        This function is called from process_access_token() inside controller
        user.py. Here we get the access token from provided user_credentials
        and auth code for fetching access token by making API call.
        :return:
        """
        data['api_relative_url'] = '/member/self'
        super(Meetup, self).get_member_id(data)

    def get_groups(self):
        """
        This function returns the groups of Meetup for which the current user
        is an organizer to be shown in drop down while creating event on Meetup
        through Event Creation Form.
        """
        function_name = 'get_groups()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
        url = self.api_url + '/groups/'
        params = {'member_id': 'self'}
        response = http_request('GET', url, params=params, headers=self.headers,
                                message_to_log=message_to_log)
        if response.ok:
            meta_data = json.loads(response.text)['meta']
            member_id = meta_data['url'].split('=')[1].split('&')[0]
            data = json.loads(response.text)['results']
            groups = filter(lambda item: item['organizer']['member_id'] == int(member_id), data)
            return groups

    def validate_token(self, payload=None):
        self.api_relative_url = '/member/self'
        return super(Meetup, self).validate_token()

    def refresh_access_token(self):
        """
        When user authorize to Meetup account, we get a refresh token
        and access token. Access token expires in one hour.
        Here we refresh the access_token using refresh_token without user
        involvement and save in user_credentials db table
        :return:
        """
        function_name = 'refresh_access_token()'
        message_to_log = get_message_to_log(function_name=function_name,
                                            class_name=self.__class__.__name__,
                                            gt_user=self.user.name,
                                            file_name=__file__)
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
                                message_to_log=message_to_log)
        try:
            if response.ok:
                # access token has been refreshed successfully, need to update
                # self.access_token and self.headers
                self.access_token = response.json().get('access_token')
                self.headers.update({'Authorization': 'Bearer ' + self.access_token})
                refresh_token = response.json().get('refresh_token')
                data = dict(user_id=self.user_credentials.user_id,
                            social_network_id=self.user_credentials.social_network_id,
                            access_token=self.access_token,
                            refresh_token=refresh_token,
                            member_id=self.user_credentials.member_id)
                status = self.save_user_credentials_in_db(data)
                logger.info("Access Token has been refreshed")
            else:
                error_message = response.json().get('error')
                message_to_log.update({'error': error_message})
                log_error(message_to_log)
        except Exception as e:
            error_message = "Error occurred while refreshing access token. Error is: " \
                            + e.message
            message_to_log.update({'error': error_message})
            log_exception(message_to_log)
        return status

if __name__ == "__main__":
    eb = Meetup(user_id=1, social_network_id=13)
    eb.process_events()
