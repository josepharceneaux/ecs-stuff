"""
This module contains Twitter class. It inherits from SocialNetworkBase class.
Currently it has only functionality related to user authentication. i.e. connecting getTalent users with their
Twitter accounts.
"""

__author__ = 'basit'

# Standard Library
import json
import base64

# Third Party
import tweepy
from flask import redirect
from contracts import contract

# Application Specific
from base import SocialNetworkBase
from social_network_service.common.redis_cache import redis_store
from social_network_service.social_network_app import app, logger
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.modules.constants import APPLICATION_BASED_AUTH_URL
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.routes import SocialNetworkApiUrl, get_web_app_url


class Twitter(SocialNetworkBase):
    """
    This class is inherited from SocialNetworkBase class.
    Developers can see the docs here http://tweepy.readthedocs.io/en/v3.5.0/auth_tutorial.html to connect
    users with their Twitter accounts.

    Here is the flow how getTalent user is connected with its Twitter account.
    1)    When user clicks on Twitter button on profile page to connect with Twitter account, endpoint
    https://127.0.0.1:8007/v1/twitter-auth is hit where we create object of this class and call its method
    authenticate(). This redirects the user to Twitter website to enter credentials and grant access to getTalent app.
    2)    Once user is successfully logged-in to Twitter account, it is redirected to the endpoint
    https://127.0.0.1:8007/v1/twitter-callback to get access token where we create object of this class and call its
    method callback().
    """
    def __init__(self, *args, **kwargs):
        super(Twitter, self).__init__(**kwargs)
        self.consumer_key = self.social_network.client_key
        if not self.consumer_key:
            raise InternalServerError('Twitter client_key not set correctly')
        self.consumer_secret = self.social_network.secret_key
        if not self.consumer_secret:
            raise InternalServerError('Twitter secret key not set correctly')
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret,
                                        SocialNetworkApiUrl.TWITTER_CALLBACK % self.user.id)

    def authenticate(self):
        """
        Here we use OAuthHandler of tweepy to give us request token. We use that request token and
        redirect the user to Twitter website where user can add its credentials.
        Once user is successfully logged-in, user is again redirected to URL as specified by callback URL of
        OAuthHandler which is http://127.0.0.1:8007/v1/twitter-callback/<int:user_id> (for local environment)
        in this case.
        In case of failure, we log the error and raises InternalServerError.

        This method is called from endpoint http://127.0.0.1:8007/v1/twitter-auth.
        """
        try:

            # redirect_url takes the user to login-page of Twitter to authorize getTalent app.
            redirect_url = self.auth.get_authorization_url()
            # Once user is successfully logged-in to Twitter account, it is redirected to callback URL where
            # we need to exchange request token with access token. This access token is used to access Twitter API.
            # So, we save request_token in the redis and retrieve this in callback() method.
            redis_store.set('twitter_request_token_%s' % self.user.id, json.dumps(self.auth.request_token))
            # redirect the user to Twitter website for authorization.
            return redirect_url
        except tweepy.TweepError:
            logger.exception('Error! Failed to get request token from Twitter for User(id:%s).' % self.user.id)
            raise InternalServerError("Couldn't connect to Twitter account.")

    @contract
    def callback(self, oauth_verifier):
        """
        This method is called from endpoint http://127.0.0.1:8007/v1/twitter-callback/<int:user_id>
        defined in app.py.
        Here we use "oauth_verifier" to get access token for the user.
        If we get any error in getting access token, we log the error and raise InternalServerError.

        Once we have the access_token, we get the member_id (id of getTalent user on Twitter's website) of user
        from Twitter API and save its credentials in database table "UserSocialNetworkCredential".

        :param string oauth_verifier: Token received from Twitter when user successfully connected to its account.
        """
        self.auth.request_token = json.loads(redis_store.get('twitter_request_token_%s' % self.user.id))
        try:
            self.auth.get_access_token(oauth_verifier)
        except tweepy.TweepError as error:
            logger.exception('Failed to get access token from Twitter for User(id:%s).Error: %s'
                             % (self.user.id, error.message))
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

        logger.info('User(id:%s) is now connected with Twitter. Member id on twitter is %s' % (self.user.id,
                                                                                               twitter_user.id))
        return redirect(get_web_app_url())

    def application_based_auth(self):
        """
        This function does application based authentication with Twitter. This do not need any user interaction
        to connect with Twitter account because it makes request on behalf of App.
        It raises InternalServerError in case authentication fails.
        Here are the detailed docs https://dev.twitter.com/oauth/application-only.
        :return: Access token for getTalent app to access Twitter's API.
        :rtype: str
        """
        combined_key = self.consumer_key + ':' + self.consumer_secret
        combined_key = base64.b64encode(combined_key)
        headers = {'Authorization': 'Basic %s' % combined_key,
                   'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials'}
        result = http_request('post', APPLICATION_BASED_AUTH_URL, headers=headers, data=data, app=app)
        if result.ok:
            logger.info('Successfully authenticated from Twitter API. User(id:%s).', self.user.id)
            access_token = result.json()['access_token']
            return access_token
        raise InternalServerError('Error Occurred while authenticating from Twitter')
