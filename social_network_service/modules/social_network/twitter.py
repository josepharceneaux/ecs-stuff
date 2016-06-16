"""
This modules contains Twitter class. It inherits from SocialNetworkBase
class. Currently it has only function relation to user authentication.
"""
__author__ = 'basit'

# Standard Library
import base64

# Third Party
import tweepy
import requests
from flask import session, redirect

# Application Specific
from base import SocialNetworkBase
from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.models.user import UserSocialNetworkCredential


class Twitter(SocialNetworkBase):
    """
    - This class is inherited from SocialNetworkBase class.
    """

    def __init__(self, *args, **kwargs):
        super(Twitter, self).__init__(**kwargs)
        self.CONSUMER_KEY = self.social_network.client_key
        self.CONSUMER_SECRET = self.social_network.secret_key
        self.auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET, SocialNetworkApiUrl.TWITTER_CALLBACK)

    def authentication(self):
        try:
            redirect_url = self.auth.get_authorization_url()
            session['request_token'] = self.auth.request_token
            # This is used in callback endpoint here /v1/twitter_callback
            session['user_id'] = self.user.id
            return redirect(redirect_url)
        except tweepy.TweepError:
            logger.exception('Error! Failed to get request token from Twitter for User(id:%s).' % self.user.id)

    def callback(self, oauth_verifier):
        self.auth.request_token = session['request_token']
        try:
            self.auth.get_access_token(oauth_verifier)
        except tweepy.TweepError:
            logger.exception('Failed to get access token from Twitter for User(id:%s).' % self.user.id)
        access_token = self.auth.access_token
        # This may be used later
        # access_token_secret = self.auth.access_token_secret
        api = tweepy.API(self.auth)
        twitter_user = api.me()
        user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(self.user.id,
                                                                                         self.social_network.id)
        if not user_credentials:
            user_credentials_obj = UserSocialNetworkCredential(user_id=self.user.id,
                                                               social_network_id=self.social_network.id,
                                                               member_id=twitter_user.id, access_token=access_token)
            UserSocialNetworkCredential.save(user_credentials_obj)

        return 'User(id:%s) is now connected with Twitter. Member id on twitter is %s' % (self.user.id,
                                                                                          twitter_user.id)

    def application_based_auth(self):
        """
        This function does application based authentication with Twitter.
        """
        combined_key = self.CONSUMER_KEY + ':' + self.CONSUMER_SECRET
        combined_key = base64.b64encode(combined_key)
        headers = {'Authorization': 'Basic %s' % combined_key,
                   'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials'}
        url = 'https://api.twitter.com/oauth2/token'
        result = requests.post(url, headers=headers, data=data)
        access_token = result.json()['access_token']
        print access_token
