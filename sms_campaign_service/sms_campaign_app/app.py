"""
    Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains sms_campaign_app startup.
    We register blueprints for different APIs with this app.
"""
import tweepy
import base64
import requests

from werkzeug.utils import redirect
from flask import request, session, render_template
from sms_campaign_service.common.routes import SmsCampaignApiUrl

# Imports for Blueprints
from api.v1_sms_campaign_api import sms_campaign_blueprint

# Register Blueprints for different APIs
from sms_campaign_service.sms_campaign_app import app
app.register_blueprint(sms_campaign_blueprint)

CONSUMER_KEY = 'C6NygfLFDsqLmbChVyKgxcxEc'
CONSUMER_SECRET = 'QNAQB3sF6IQsDJO24SczVMOMIPFMDdMPAUvLOMoOMh8pERrKiH'


@app.route('/')
def root():
    # from flask import render_template
    # timestamp = DatetimeUtils.unix_time(datetime.utcnow().replace(tzinfo=pytz.utc))
    # url = 'https://api.twitter.com/oauth/request_token'
    # headers = {'Authorization': 'OAuth oauth_consumer_key="%s", oauth_nonce="%s", '
    #                             'oauth_signature="%s", '
    #                             'oauth_signature_method="HMAC-SHA1", '
    #                             'oauth_timestamp="%s", '
    #                             'oauth_version="1.0"' % (CONSUMER_KEY, fake.word(),
    #                                                      "%2F29WzMjMcGd7g2RCHO6tJ9Bv%2B4M%3D", timestamp)}
    # response = requests.post(url, headers=headers)
    # access_token = response.text.split('oauth_token=')[1].split('oauth_token_secret=')[0]
    # print access_token
    #
    return render_template('index.html')
    # return 'Welcome to SMS Campaign Service'


@app.route('/twitter_auth')
def twitter_auth():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, SmsCampaignApiUrl.HOST_NAME % '/twitter_callback')
    try:
        redirect_url = auth.get_authorization_url()
        session['request_token'] = auth.request_token
        return redirect(redirect_url)
    except tweepy.TweepError:
        print 'Error! Failed to get request token.'


@app.route('/twitter_callback')
def callback():
    oauth_verifier = request.args['oauth_verifier']
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.request_token = session['request_token']
    try:
        auth.get_access_token(oauth_verifier)
    except tweepy.TweepError:
        print 'Error! Failed to get access token.'
    access_token = auth.access_token
    access_token_secret = auth.access_token_secret
    print access_token
    print access_token_secret
    api = tweepy.API(auth)
    user = api.me()
    return 'User(id:%s) is now connected with Twitter.' % user.id


def application_based_auth():
    """
    This function does application based authentication with Twitter.
    """
    combined_key = CONSUMER_KEY + ':' + CONSUMER_SECRET
    combined_key = base64.b64encode(combined_key)
    headers = {'Authorization': 'Basic %s' % combined_key,
               'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials'}
    url = 'https://api.twitter.com/oauth2/token'
    result = requests.post(url, headers=headers, data=data)
    access_token = result.json()['access_token']
    print access_token
