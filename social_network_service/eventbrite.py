from base import SocialNetworkBase
from common.models.user import UserCredentials
from utilities import http_request, log_exception, log_error

# TODO: Will replace this ULR with actual webhook URL (Flask App)
WEBHOOK_REDIRECT_URL = 'http://4ddd1621.ngrok.io'


class Eventbrite(SocialNetworkBase):

    def __init__(self, *args, **kwargs):
        super(Eventbrite, self).__init__(*args, **kwargs)

    @classmethod
    def get_access_token(cls, data, relative_url=None):
        """
        This function is called from process_access_token() inside controller
        user.py. Here we get the access token from provided user_credentials
        and auth code for fetching access token by making API call.
        :return:
        """
        data = dict(api_relative_url="/token")
        super(Eventbrite, cls).get_access_token(data)

    def get_member_id(self, data):
        """
        This function is called from process_access_token() inside controller
        user.py. Here we get the access token from provided user_credentials
        and auth code for fetching access token by making API call.
        :return:
        """
        data['api_relative_url'] = "/users/me/"
        super(Eventbrite, self).get_member_id(data)

    def validate_token(self, payload=None):
        self.api_relative_url = '/users/me/'
        super(Eventbrite, self).validate_token()

    @staticmethod
    def save_token_in_db(user_credentials):

        # now we create webhook for eventbrite user for getting rsvp through webhook
        # via EventService app
        super(Eventbrite, Eventbrite).save_user_credentials_in_db(user_credentials)
        Eventbrite.create_webhook(user_credentials)

    @staticmethod
    def create_webhook(user_credentials):
        """
        Creates a webhook to stream the live feed of Eventbrite users to the
        Flask app. It gets called in the save_token_in_db().
        It takes user_credentials to save webhook against that user.
        Here it performs a check which ensures  that webhook is not generated
        every time code passes through this flow once a webhook has been
        created for a user (since webhooks don't expire and are unique for
        every user).
        :return: True if webhook creation is successful o/w False
        """
        user_credentials_in_db = UserCredentials.get_by_user_and_social_network_id(
            user_credentials['userId'],
            user_credentials['socialNetworkId'])
        if user_credentials_in_db.webhook in [None, '']:
            url = user_credentials_in_db.socialNetwork.apiUrl + "/webhooks/"
            payload = {'endpoint_url': WEBHOOK_REDIRECT_URL}
            response = http_request('POST', url, payload, user_id=user_credentials['userId'])
            if response.ok:
                try:
                    webhook_id = response.json()['id']
                    user_credentials_in_db.update(webhook=webhook_id)
                except Exception as e:
                    error_message = e.message
                    log_exception({'user_id':user_credentials['userId'],
                                   'error': error_message})
            else:
                error_message = "Webhook was not created successfully."
                log_error({'user_id':user_credentials['userId'],
                           'error': error_message})

# if __name__ == "__main__":
#     eb = Eventbrite(user_id=1, social_network_id=18)
#     eb.process_events()
