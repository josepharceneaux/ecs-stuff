"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# 3rd party imports
from flask import request, redirect
from flask.ext.graphql import GraphQLView

# Application specific imports
from ..social_network_app import app, logger
from restful.v1_data import data_blueprint
from restful.v1_importer import rsvp_blueprint
from restful.v1_events import events_blueprint
from restful.v1_subscription import subscription_blueprint
from social_network_service.tasks import fetch_eventbrite_event
from social_network_service.common.talent_api import TalentApi
from restful.v1_social_networks import social_network_blueprint
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.constants import MEETUP, EVENTBRITE
from social_network_service.modules.constants import MEETUP_CODE_LENGTH, ACTIONS
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.modules.social_network.twitter import Twitter
from social_network_service.social_network_app.graphql.schema import schema
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.routes import SocialNetworkApiUrl, SocialNetworkApi
from social_network_service.common.talent_config_manager import (TalentEnvs, TalentConfigKeys)

# Register Blueprints for different APIs
app.register_blueprint(data_blueprint)
app.register_blueprint(rsvp_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(subscription_blueprint)
app.register_blueprint(social_network_blueprint)
api = TalentApi(app)

# Initialize Redis Cache
redis_store.init_app(app)

app.add_url_rule(SocialNetworkApi.GRAPHQL,
                 view_func=require_oauth()(
                     GraphQLView.as_view('graphql', schema=schema,
                                         graphiql=app.config[TalentConfigKeys.ENV_KEY] == TalentEnvs.DEV)))


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
        social_network = SocialNetwork.get_by_name(MEETUP.title())
    else:
        social_network = SocialNetwork.get_by_name(EVENTBRITE.title())
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


@app.route(SocialNetworkApi.WEBHOOK, methods=['POST'])
def eventbrite_webhook_endpoint(user_id):
    data = request.json
    action_type = data['config']['action']
    member_id = data['config']['user_id']
    event_url = data['api_url']
    if action_type != ACTIONS['updated']:
        logger.info('Eventbrite Alert, Event: %s' % data)
        fetch_eventbrite_event.apply_async((user_id, member_id, event_url, action_type))
    return 'Thanks a lot!'
