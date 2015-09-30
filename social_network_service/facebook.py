import os
from gt_common.models.config import GTSQLAlchemy
app_cfg = os.path.abspath('app.cfg')
logging_cfg = os.path.abspath('logging.conf')

gt = GTSQLAlchemy(app_config_path=app_cfg,
                  logging_config_path=logging_cfg)

from social_network_service.base import SocialNetworkBase


class Facebook(SocialNetworkBase):

    def __init__(self, *args, **kwargs):

        super(Facebook, self).__init__(*args, **kwargs)
        # token validity is checked here
        # if token is expired, we refresh it here
        self.validate_and_refresh_access_token()

    @classmethod
    def get_access_token(cls, code_to_get_access_token, relative_url=None):
        """
        This function is called from process_access_token() inside controller
        user.py. Here we get the access token from provided user_credentials
        and auth code for fetching access token by making API call.
        :return:
        """
        pass

    def validate_token(self, payload=None):
        self.api_relative_url = '/me'
        payload = {'access_token': self.access_token}

        super(Facebook, self).validate_token(payload=payload)
if __name__ == "__main__":
    eb = Facebook(user_id=1, social_network_id=2)
    eb.process_events()