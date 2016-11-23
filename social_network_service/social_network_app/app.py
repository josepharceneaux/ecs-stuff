"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# 3rd party imports
from flask import request, redirect, jsonify
from flask.ext.graphql import GraphQLView

# Application specific imports
from ..social_network_app import app, logger
from restful.v1_data import data_blueprint
from restful.v1_importer import rsvp_blueprint
from restful.v1_events import events_blueprint
from restful.v1_subscription import subscription_blueprint
from social_network_service.common.talent_api import TalentApi
from restful.v1_social_networks import social_network_blueprint
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.constants import MEETUP, EVENTBRITE
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.modules.social_network.twitter import Twitter
from social_network_service.social_network_app.graphql.schema import schema
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.routes import SocialNetworkApiUrl, SocialNetworkApi
from social_network_service.common.talent_config_manager import (TalentEnvs, TalentConfigKeys)
from social_network_service.tasks import (import_eventbrite_event, process_meetup_event,
                                          process_meetup_rsvp, process_eventbrite_rsvp)
from social_network_service.modules.constants import (MEETUP_CODE_LENGTH, ACTIONS, EVENTBRITE_USER_AGENT, EVENT, RSVP)


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
    error = request.args.get('error')
    if error:
        return redirect(SocialNetworkApiUrl.SUBSCRIBE % error)
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
    """
    This endpoint is for Eventbrite webhook. We have registered `publish` and `unpublish` events for
    events. So when a subscribed/connected user creates or deletes an event, Eventbrite sends event info
    on this endpoint with action information.

    Webhook returns data for RSVP as:
        {
            u'config': {u'action': u'order.placed', u'user_id': u'149011448333',
            u'endpoint_url': u'https://emails.ngrok.io/webhook/1', u'webhook_id': u'274022'},
            u'api_url': u'https://www.eventbriteapi.com/v3/orders/573384540/'
        }

    :param int | long user_id: user unique id
    """
    logger.info('Webhook Endpoint: Received a request with this data: %s' % request.data)
    if EVENTBRITE_USER_AGENT in str(request.user_agent):
        data = request.json
        action_type = data['config']['action']
        event_url = data['api_url']
        if action_type in [ACTIONS['published'], ACTIONS['unpublished']]:
            logger.info('Eventbrite Alert, Event: %s' % data)
            import_eventbrite_event.apply_async((user_id, event_url, action_type))
        if action_type in [ACTIONS['rsvp'], ACTIONS['rsvp_updated']]:
            if action_type == ACTIONS['rsvp']:
                logger.info('Eventbrite Alert, RSVP: %s' % data)
                process_eventbrite_rsvp.delay(data)
            elif action_type == 'test':
                logger.debug('Successful webhook connection')
    return 'Thanks a lot!'


@app.route(SocialNetworkApi.MEETUP_IMPORTER, methods=['POST'])
def meetup_importer_endpoint():
    """
    This endpoint will act as webhook for Meetup Events and RSVPs
    On receiving POST request, we will call specific celery task to process Event or RSVP data.
    """
    data = request.json
    if data.get('type') == EVENT:
        event = data['event']
        logger.info('Got Meetup event: %s' % event)
        process_meetup_event.delay(event)
    elif data.get('type') == RSVP:
        rsvp = data['rsvp']
        logger.info('Got Meetup RSVP: %s' % rsvp)
        process_meetup_rsvp.delay(rsvp)
    return jsonify(dict(message='Thanks a lot!'))
