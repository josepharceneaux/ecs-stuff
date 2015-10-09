import re
import json
import flask
import requests
from social_network_service import init_app
from social_network_service.eventbrite import Eventbrite

app = init_app()

from restful.events import events_blueprint
from restful.social_networks import social_network_blueprint
from social_network_service import logger
from social_network_service.app.app_utils import ApiResponse
from social_network_service.app.restful.data import data_blueprint
from social_network_service.custom_exections import ApiException
from social_network_service.rsvp.eventbrite import Eventbrite as EventbriteRsvp
from social_network_service.utilities import log_exception, get_class, log_error


from flask.ext.restful import Api
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash


# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

CLIENT_ID = 'o0nptnl4eet4c40suj9es52612'
CLIENT_SECRET = 'ohtutvn34cvfucl26i5ele5ki2'
REDIRECT_URL = 'http://127.0.0.1:5000/code'
user_refresh_token = '73aac7b76040a33d5dda70d0190aa4e7'
EVENTBRITE = 'Eventbrite'

app.register_blueprint(social_network_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(data_blueprint)
api = Api(app)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


# @app.errorhandler(404)
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


@app.route('/test/<access_token>')
def get_member_id(access_token):
    if token_validity(access_token):
        token = access_token
    else:
        token = refresh_token()
    header = {'Authorization': 'Bearer ' + token}
    result = requests.get("https://api.meetup.com/2/member/self",
                          headers=header)
    if result.ok:
        message = 'MemberId: %s' % result.json()['id']
    else:
        message = result.json()['problem'], result.json()['details']
    data = {'message': message}
    return json.dumps(data)


@app.route('/meetup_authorization')
def meetup_authorization():
    return redirect("https://secure.meetup.com/oauth2/authorize?"
                    "client_id=%s"
                    "&response_type=code"
                    "&redirect_uri=%s" % (CLIENT_ID, REDIRECT_URL))


@app.route('/code')
def code():
    if request.args.get('code'):
        received_code = request.args['code']
        response = requests.post("https://secure.meetup.com/oauth2/access?"
                                 "client_id=%s"
                                 "&client_secret=%s"
                                 "&grant_type=authorization_code"
                                 "&redirect_uri=%s"
                                 "&code=%s"
                                 % (CLIENT_ID, CLIENT_SECRET, REDIRECT_URL,
                                    received_code))
        if response.ok:
            access_token = response.json()['access_token']
            user_refresh_token = response.json()['refresh_token']
            # save access_token and refresh token in database
            message = {'access_token': access_token,
                       'refresh_token': user_refresh_token}
        else:
            message = {'Error': response.json()['error']}
        return json.dumps(message)


def refresh_token():
    response = requests.post("https://secure.meetup.com/oauth2/access?"
                             "&client_id=%s"
                             "&client_secret=%s"
                             "&grant_type=refresh_token"
                             "&refresh_token=%s" % (CLIENT_ID,
                                                    CLIENT_SECRET,
                                                    user_refresh_token))
    if response.ok:
        access_token = response.json()['access_token']
        return access_token


def token_validity(access_token):
    header = {'Authorization': 'Bearer ' + access_token}
    result = requests.get("https://api.meetup.com/2/member/self", headers=header)
    if result.ok:

        return True
    else:
        return False


@app.route('/rsvp', methods=['GET', 'POST'])
def handle_rsvp():
    """
    This function Only receives data when a candidate rsvp to some event.
    It first find the getTalent user having incoming webhook id.
    Then it creates the candidate in candidate table by getting information
    of attendee. Then it inserts in rsvp table the required information.
    It will also insert an entry in DB tables candidate_event_rsvp and activity
    """
    # hub_challenge = request.args['hub.challenge']
    # verify_token = request.args['hub.verify_token']
    # hub_mode = request.args['hub.mode']
    # assert verify_token == 'token'
    user_id = ''
    try:
        if request.data:
            data = json.loads(request.data)
            action = data['config']['action']
            if action == 'order.placed':
                logger.debug('Got an RSVP from eventbrite event via webhook.')
                webhook_id = data['config']['webhook_id']
                user_credentials = \
                    EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)
                user_id = user_credentials.user_id
                social_network_class = \
                    get_class(user_credentials.social_network.name.lower(),
                              'social_network')
                # we call social network class here for auth purpose, If token is
                # expired, we try to refresh access token. If succeeded, we move on
                # to next step.
                sn_obj = social_network_class(user_id=user_credentials.user_id)
                if not user_credentials.member_id:
                    # get an save the member Id of gt-user
                    sn_obj.get_member_id()
                sn_obj.process('rsvp', user_credentials=user_credentials, rsvp_data=data)
            elif action == 'test':
                logger.debug('Successful Webhook Connection')
        else:
            # return hub_challenge, 200
            error_message = 'No RSVP Data Received'
            log_error({'user_id': user_id,
                       'error': error_message})
            data = {'message': error_message,
                    'status_code': 500}
            return flask.jsonify(**data), 500
    except Exception as error:
        log_exception({'user_id': user_id,
                       'error': error.message})
        data = {'message': error.message,
                'status_code': 500}
        return flask.jsonify(**data), 500

    data = {'message': 'RSVP Saved',
            'status_code': 200}
    return flask.jsonify(**data), 200


@app.errorhandler(ApiException)
def handle_api_exception(error):
    response = json.dumps(error.to_dict())
    return ApiResponse(response, status=error.status_code)


@app.errorhandler(Exception)
def handle_any_errors(error):
    response = json.dumps(dict(message='Ooops! Internal server error occurred..'))
    return ApiResponse(response, status=500)

# app = Flask(__name__)
# app.config.from_object('social_network_service.config')

# db.init_app(app)
# db.app = app
#
# from common.error_handling import register_error_handlers
# register_error_handlers(app, logger)

# @app.teardown_request
# def teardown_request(exception=None):
#     db_session.remove()

