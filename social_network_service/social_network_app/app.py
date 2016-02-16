"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard imports
import json
import traceback

# 3rd party imports
import flask
from flask import request, redirect

# Application specific imports

from restful.v1_data import data_blueprint
from restful.v1_events import events_blueprint
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.routes import SocialNetworkApiUrl, SocialNetworkApi
from social_network_service.social_network_app import app, logger
from social_network_service.modules.utilities import get_class
from restful.v1_social_networks import social_network_blueprint
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.modules.rsvp.eventbrite import Eventbrite as EventbriteRsvp

# Register Blueprints for different APIs
app.register_blueprint(data_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(social_network_blueprint)

api = TalentApi(app)

# Initialize Redis Cache
redis_store.init_app(app)

# TODO: remove this in final code
WEBHOOK_REDIRECT_URL = 'https://729c03b1.ngrok.io'


@app.route('/')
def index():
    return 'Welcome to social network service'

# TODO: add comment
@app.route(SocialNetworkApi.CODE)
def authorize():
    code = request.args.get('code')
    url = SocialNetworkApiUrl.UI_APP_URL + '/campaigns/events/subscribe?code=%s' % code
    if 'state' in request.args:
        social_network = SocialNetwork.get_by_name('Meetup')
    else:
        social_network = SocialNetwork.get_by_name('Eventbrite')
    url += '&id=%s' % social_network.id
    return redirect(url)


@app.route(SocialNetworkApi.RSVP, methods=['GET', 'POST'])
def handle_rsvp():
    """
    This function only receives data when a candidate rsvp to some event.
    It first finds the getTalent user having incoming webhook id.
    Then it creates the candidate in candidate table by getting information
    of attendee. Then it inserts in rsvp table the required information.
    It will also insert an entry in DB table activity
    """
    # hub_challenge = request.args['hub.challenge']
    # verify_token = request.args['hub.verify_token']
    # hub_mode = request.args['hub.mode']
    # assert verify_token == 'token'
    user_id = ''
    if request.data:
        try:
            data = json.loads(request.data)
            action = data['config']['action']
            if action == 'order.placed':
                webhook_id = data['config']['webhook_id']
                user_credentials = \
                    EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)
                logger.debug('Got an RSVP on %s Event via webhook.'
                             % user_credentials.social_network.name)
                user_id = user_credentials.user_id
                social_network_class = \
                    get_class(user_credentials.social_network.name.lower(),
                              'social_network')
                # we make social network object here to check the validity of
                # access token. If access token is valid, we proceed to do the
                # processing to save in getTalent db tables otherwise we raise
                # exception AccessTokenHasExpired.
                sn_obj = social_network_class(user_id=user_credentials.user_id)
                sn_obj.process('rsvp', user_credentials=user_credentials,
                               rsvp_data=data)
            elif action == 'test':
                logger.debug('Successful webhook connection')

        except Exception as error:
            logger.exception('handle_rsvp: Request data: %s, user_id: %s',
                             request.data, user_id)
            data = {'message': error.message,
                    'status_code': 500}
            return flask.jsonify(**data), 500

        data = {'message': 'RSVP Saved',
                'status_code': 200}
        return flask.jsonify(**data), 200

    else:
        # return hub_challenge, 200
        error_message = 'No RSVP data received.'
        data = {'message': error_message,
                'status_code': 200}
        return flask.jsonify(**data), 200

