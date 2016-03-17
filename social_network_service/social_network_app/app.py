"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard imports
import json

# 3rd party imports
import flask
from flask import request, redirect

# Application specific imports

from restful.v1_data import data_blueprint
from restful.v1_events import events_blueprint
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.routes import SocialNetworkApiUrl, SocialNetworkApi, get_webhook_app_url
from social_network_service.social_network_app import app, logger
from social_network_service.modules.utilities import get_class
from restful.v1_social_networks import social_network_blueprint
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.modules.rsvp.eventbrite import Eventbrite as EventbriteRsvp

# Register Blueprints for different APIs
from social_network_service.social_network_app.restful.v1_importer import rsvp_blueprint

app.register_blueprint(data_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(social_network_blueprint)
app.register_blueprint(rsvp_blueprint)

api = TalentApi(app)

# Initialize Redis Cache
redis_store.init_app(app)


WEBHOOK_REDIRECT_URL = get_webhook_app_url()


@app.route('/')
def index():
    return 'Welcome to social network service'


@app.route(SocialNetworkApi.CODE)
def authorize():
    """
    This is a redirect URL which will be hit when a user accept the invitation on meetup or eventbrite
    In case of meetup the querystring args contain 'state'
    and in case of eventbrite the querystring args does not contain 'state' parameter
    :return:
    """
    code = request.args.get('code')
    url = SocialNetworkApiUrl.UI_APP_URL + '/campaigns/events/subscribe?code=%s' % code
    if 'state' in request.args:
        social_network = SocialNetwork.get_by_name('Meetup')
    else:
        social_network = SocialNetwork.get_by_name('Eventbrite')
    url += '&id=%s' % social_network.id
    return redirect(url)

