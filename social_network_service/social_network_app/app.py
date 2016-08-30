"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""

# 3rd party imports
from flask import request, redirect

# Application specific imports
from restful.v1_data import data_blueprint
from restful.v1_events import events_blueprint
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.routes import SocialNetworkApiUrl, SocialNetworkApi
from social_network_service.mock.mock_service import mock_blueprint
from social_network_service.modules.constants import MEETUP_CODE_LENGTH
from social_network_service.modules.social_network.twitter import Twitter
from social_network_service.modules.urls import SocialNetworkUrls
from social_network_service.social_network_app import app
from restful.v1_social_networks import social_network_blueprint
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.social_network_app.restful.v1_importer import rsvp_blueprint

# Register Blueprints for different APIs

app.register_blueprint(data_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(social_network_blueprint)
app.register_blueprint(rsvp_blueprint)
if SocialNetworkUrls.IS_DEV:
    app.register_blueprint(mock_blueprint)

api = TalentApi(app)

# Initialize Redis Cache
redis_store.init_app(app)


@app.route('/')
def index():
    return 'Welcome to social network service'


@app.route(SocialNetworkApi.CODE)
def authorize():
    """
    This is a redirect URL which will be hit when a user accept the invitation on meetup or eventbrite
    In case of meetup the querystring args contain 'state'
    and in case of eventbrite the querystring args does not contain 'state' parameter
    """
    code = request.args.get('code')
    url = SocialNetworkApiUrl.SUBSCRIBE % code
    if len(code) == MEETUP_CODE_LENGTH:
        social_network = SocialNetwork.get_by_name('Meetup')
    else:
        social_network = SocialNetwork.get_by_name('Eventbrite')
    url += '&id=%s' % social_network.id
    return redirect(url)


@app.route(SocialNetworkApi.TWITTER_CALLBACK)
def callback(user_id):
    """
    Once user is successfully logged-in to Twitter account, it is redirected to this endpoint to get access token,
    Here we create object of Twitter class defined in social_network/twitter.py and call its method callback().
    In request object, we get a parameter "oauth_verifier" which we use to get access token for the user.
    **See Also**
        .. seealso:: callback() method defined in Twitter class inside social_network/twitter.py.
    """
    if 'oauth_verifier' in request.args:
        twitter_obj = Twitter(user_id=user_id, validate_credentials=False)
        return twitter_obj.callback(request.args['oauth_verifier'])
    raise InternalServerError('You did not provide valid credentials. Unable to connect! Please try again.')
