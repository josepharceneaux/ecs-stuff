"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard imports
import json
import traceback
import flask

# init APP
# This line should come before any imports from models
from social_network_service import init_app
app = init_app()

# 3rd party imports
from flask import request
from flask.ext.cors import CORS
from flask.ext.restful import Api

# Application specific imports
from social_network_service import logger
from social_network_service.app.app_utils import ApiResponse
from social_network_service.custom_exections import ApiException
from social_network_service.app.restful.data import data_blueprint
from social_network_service.custom_exections import AccessTokenHasExpired
from social_network_service.rsvp.eventbrite import Eventbrite as EventbriteRsvp
from restful.events import events_blueprint
from social_network_service.utilities import get_class
from social_network_service.utilities import log_exception
from restful.social_networks import social_network_blueprint

# Register Blueprints for different APIs
app.register_blueprint(social_network_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(data_blueprint)
api = Api(app)


# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


@app.route('/')
def hello_world():
    # return 'Hello World!', 404
    try:
        from common.models.candidate import Candidate
        from common.models.event import Event
        candidate = Candidate.query.all()[0]
        event = Event.query.all()[0]
    except Exception as error:
        import traceback
        return traceback.format_exc()
    return 'Hello World! %s, %s' % (candidate.first_name, event.title)


@app.route('/rsvp', methods=['GET', 'POST'])
def handle_rsvp():
    """
    This function only receives data when a candidate rsvp to some event.
    It first finds the getTalent user having incoming webhook id.
    Then it creates the candidate in candidate table by getting information
    of attendee. Then it inserts in rsvp table the required information.
    It will also insert an entry in DB tables candidate_event_rsvp and activity
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
                logger.debug('Got an RSVP from Eventbrite event via webhook.')
                webhook_id = data['config']['webhook_id']
                user_credentials = \
                    EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)
                user_id = user_credentials.user_id
                social_network_class = \
                    get_class(user_credentials.social_network.name.lower(),
                              'social_network')
                # we make social network object here to check the validity of
                # access token. If access token is valid, we proceed to do the
                # processing to save in getTalent db tables otherwise we raise
                # exception AccessTokenHasExpired.
                sn_obj = social_network_class(user_id=user_credentials.user_id)
                if sn_obj.access_token_status:
                    sn_obj.process('rsvp', user_credentials=user_credentials,
                                   rsvp_data=data)
                else:
                    raise AccessTokenHasExpired(
                        'Access token has expired. Please connect with %s again '
                        'from "Profile" page.' % user_credentials.social_network.name)

            elif action == 'test':
                logger.debug('Successful webhook connection')

        except Exception as error:
            log_exception({'user_id': user_id,
                           'error': error.message})
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


@app.errorhandler(ApiException)
def handle_api_exception(error):
    """
    This handler handles ApiException error
    :param error: exception object containing error info
    :type error:  ApiException
    :return: json response
    """
    logger.debug('Error: %s\nTraceback: %s' % (error, traceback.format_exc()))
    response = json.dumps(error.to_dict())
    return ApiResponse(response, status=error.status_code)


@app.errorhandler(Exception)
def handle_any_errors(error):
    """
    This handler handles any kind of error in app.
    :param error: exception object containing error info
    :type error:  Exception
    :return: json response
    """
    logger.debug('Error: %s\nTraceback: %s' % (error, traceback.format_exc()))
    response = json.dumps(dict(message='Ooops! Internal server error occurred..' + error.message))
    return ApiResponse(response, status=500)

