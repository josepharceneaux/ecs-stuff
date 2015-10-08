import json

from base import SocialNetworkBase
from utilities import http_request, logger, log_error, log_exception


class Meetup(SocialNetworkBase):

    def __init__(self, *args, **kwargs):
        super(Meetup, self).__init__(*args, **kwargs)

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
        url = self.api_url + '/groups/'
        params = {'member_id': 'self'}
        response = http_request('GET', url, params=params, headers=self.headers,
                                user_id=self.user.id)
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
                data = dict(user_id=self.user_credentials.user_id,
                            social_network_id=self.user_credentials.social_network_id,
                            access_token=self.access_token,
                            refresh_token=refresh_token,
                            member_id=self.user_credentials.member_id)
                status = self.save_user_credentials_in_db(data)
                logger.debug("Access token has been refreshed for %s(UserId:%s)."
                             % (self.user.name, self.user.id))
            else:
                error_message = response.json().get('error')
                log_error({'user_id': self.user.id,
                           'error': error_message})
        except Exception as e:
            error_message = "Error occurred while refreshing access token. Error is: " \
                            + e.message
            log_exception({'user_id': self.user.id,
                           'error': error_message})
        return status

# if __name__ == "__main__":
#     eb = Meetup(user_id=1, social_network_id=13)
#     eb.process_events()
