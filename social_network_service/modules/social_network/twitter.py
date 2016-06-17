"""
This modules contains Twitter class. It inherits from SocialNetworkBase class.
Currently it has only functionality related to user authentication. i.e. connecting getTalent users with their
Twitter accounts.
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
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.models.user import UserSocialNetworkCredential


class Twitter(SocialNetworkBase):
    """
    This class is inherited from SocialNetworkBase class.
    Developers can see the docs here http://tweepy.readthedocs.io/en/v3.5.0/auth_tutorial.html to connect
    users with their Twitter accounts.
    """

    def __init__(self, *args, **kwargs):
        super(Twitter, self).__init__(**kwargs)
        self.CONSUMER_KEY = self.social_network.client_key
        self.CONSUMER_SECRET = self.social_network.secret_key
        self.auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET, SocialNetworkApiUrl.TWITTER_CALLBACK)

    def authentication(self):
        """
        Here we use OAuthHandler of tweepy to give us request token. We use that request token and
        redirect the user to Twitter website where user can add its credentials.
        Once user is successfully logged-in, user is again redirected to URL as specified by callback URL of
        OAuthHandler which is http://127.0.0.1:8007/v1/twitter_callback (for local environment) in this case.
        In case of failure, we log the error and raises InternalServerError.

        This method is called from endpoint http://127.0.0.1:8007/v1/twitter_auth defined in app.py
        """
        try:
            # redirect_url takes the user to login-page of Twitter to authorize getTalent app.
            redirect_url = self.auth.get_authorization_url()
            # Once user is successfully logged-in to Twitter account, it is redirected to callback URL where
            # we need to exchange request token with access token. This access token is used to access Twitter API.
            # So, we save request_token in the session and retrieve this in callback() method.
            session['request_token'] = self.auth.request_token
            # This is used in callback endpoint here /v1/twitter_callback. We need user_id there to create object
            # of Twitter class.
            session['user_id'] = self.user.id
            # redirect the user to Twitter website for authorization.
            return redirect(redirect_url)
        except tweepy.TweepError:
            logger.exception('Error! Failed to get request token from Twitter for User(id:%s).' % self.user.id)
            raise InternalServerError("Couldn't connect to Twitter account.")

    def callback(self, oauth_verifier):
        """
        This method is called from endpoint http://127.0.0.1:8007/v1/twitter_callback defined in app.py
        Here we use "oauth_verifier" to get access token for the user.
        If we get any error in getting access token, we log the error and raise InternalServerError.

        Once we have the access_token, we get the member_id (id of getTalent user on Twitter's website) of user
        from Twitter API and save its credentials in database table "UserSocialNetworkCredential".

        :param str oauth_verifier: Token received from Twitter when user successfully connected to its account.
        """
        if not isinstance(oauth_verifier, str):
            raise InternalServerError('oauth_verifier must be non-empty string')
        self.auth.request_token = session['request_token']
        try:
            self.auth.get_access_token(oauth_verifier)
        except tweepy.TweepError:
            logger.exception('Failed to get access token from Twitter for User(id:%s).' % self.user.id)
            raise InternalServerError('Failed to get access token from Twitter')

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
        This function does application based authentication with Twitter. This do not need any user interaction
        to connect with Twitter account because it makes request on behalf of App.
        Here are the detailed docs https://dev.twitter.com/oauth/application-only.
        :return: Access token for getTalent app to access Twitter's API.
        :rtype: str
        """
        combined_key = self.CONSUMER_KEY + ':' + self.CONSUMER_SECRET
        combined_key = base64.b64encode(combined_key)
        url = 'https://api.twitter.com/oauth2/token'
        headers = {'Authorization': 'Basic %s' % combined_key,
                   'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials'}
        result = requests.post(url, headers=headers, data=data)
        access_token = result.json()['access_token']
        return access_token
