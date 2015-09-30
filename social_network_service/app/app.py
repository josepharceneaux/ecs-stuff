import json
import os
import re
import flask
import requests
from social_network_service.app.app_utils import ApiResponse
from social_network_service.app.restful.data import data_blueprint
from social_network_service.custom_exections import ApiException
from social_network_service.rsvp.eventbrite import EventbriteRsvp
from restful.social_networks import social_network_blueprint
from restful.events import events_blueprint
from gt_common.models.config import db_session
from flask.ext.restful import Api
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash

# configuration
from social_network_service.utilities import log_exception, get_class, logger, get_message_to_log, log_error

DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
api = Api(app)
app.config.from_object(__name__)

CLIENT_ID = 'o0nptnl4eet4c40suj9es52612'
CLIENT_SECRET = 'ohtutvn34cvfucl26i5ele5ki2'
REDIRECT_URL = 'http://127.0.0.1:5000/code'
user_refresh_token = '73aac7b76040a33d5dda70d0190aa4e7'
EVENTBRITE = 'Eventbrite'

app.register_blueprint(social_network_blueprint)
app.register_blueprint(events_blueprint)
app.register_blueprint(data_blueprint)


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
    return 'Hello World!'


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
    function_name = 'handle_rsvp()'
    message_to_log = get_message_to_log(function_name=function_name,
                                        file_name=__file__)
    try:
        if request.data:
            data = json.loads(request.data)
            action = data['config']['action']
            if action == 'order.placed':
                url_of_rsvp = str(json.loads(request.data)['api_url'])
                # gets dictionary object of vendor_rsvp_id
                rsvp = get_rsvp_id(url_of_rsvp)
                webhook_id = data['config']['webhook_id']
                user_credentials = EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)
                social_network_class = get_class(user_credentials.social_network.name.lower(),
                                                 'social_network')
                rsvp_class = get_class(user_credentials.social_network.name.lower(), 'rsvp')
                # we call social network class here for auth purpose, If token is expired
                # access token is refreshed and we use fresh token
                sn = social_network_class(user_id=user_credentials.userId,
                                          social_network_id=user_credentials.social_network.id)
                if not user_credentials.memberId:
                    # get an save the member Id of gt-user
                    sn.get_member_id(dict())
                rsvp_obj = rsvp_class(user_credentials=user_credentials,
                                      social_network=user_credentials.social_network,
                                      headers=sn.headers,
                                      message_to_log=sn.message_to_log)
                # calls class method to process RSVP
                rsvp_obj._process_rsvp_via_webhook(rsvp)
            elif action == 'test':
                print 'Successful Webhook Connection'
        else:
            # return hub_challenge, 200
            error_message = 'No RSVP Data'
            message_to_log.update({'error': error_message})
            log_error(message_to_log)
            data = {'message': 'No RSVP Data',
                    'status_code': 500}
            return flask.jsonify(**data), 500
    except Exception as e:
        error_message = e.message
        message_to_log.update({'error': error_message})
        log_exception(message_to_log)
        data = {'message': e.message,
                'status_code': 500}
        return flask.jsonify(**data), 500

    data = {'message': 'RSVP Saved',
            'status_code': 200}
    return flask.jsonify(**data), 200


def get_rsvp_id(url):
    """
    This gets the vendor_rsvp_id by comparing url of response of rsvp
    and defined regular expression
    :return:
    """
    assert url is not None
    regex_to_get_rsvp_id = \
        '^https:\/\/www.eventbriteapi.com\/v3\/orders\/(?P<rsvp_id>[0-9]+)'
    match = re.match(regex_to_get_rsvp_id, url)
    vendor_rsvp_id = match.groupdict()['rsvp_id']
    rsvp = {'rsvp_id': vendor_rsvp_id}
    return rsvp


@app.errorhandler(ApiException)
def handle_api_exception(error):
    response = json.dumps(error.to_dict())
    return ApiResponse(response, status=error.status_code)


@app.errorhandler(Exception)
def handle_any_errors(error):
    response = json.dumps(dict(message='Ooops! Internal server error occurred..'))
    return ApiResponse(response, status=500)


@app.teardown_request
def teardown_request(exception=None):
    db_session.remove()

if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(port=5000)