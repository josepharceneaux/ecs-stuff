import json
import re
import flask
import requests
from flask_restful import Resource
from custom_exections import InvalidUsage, ApiException
from restful.social_networks import social_network_blueprint
from .restful.events import events_blueprint
from event_importer.base import logger
from event_importer.eventbrite import Eventbrite
from event_importer.meetup import Meetup
from event_importer.facebook_ev import Facebook
from gt_models.event import Event
from gt_models.user import UserCredentials
from gt_models.social_network import SocialNetwork
from gt_models.config import db_session
from flask.ext.restful import Api
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash

# configuration
from event_importer.utilities import log_exception

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

app.register_blueprint(social_network_blueprint)
app.register_blueprint(events_blueprint)
myapp = app

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
    if request.data:
        # creating object of Eventbrite class
        eventbrite_rsvp = Eventbrite()
        try:
            data = json.loads(request.data)
            action = data['config']['action']
            if action == 'order.placed':
                webhook_id = data['config']['webhook_id']
                url_of_rsvp = str(json.loads(request.data)['api_url'])

                # gets dictionary object of social_network_rsvp_id
                rsvp = get_rsvp_id(url_of_rsvp)

                eventbrite_rsvp.webhook_id = webhook_id

                # getting data of gt-user of Get Talent
                # gets gt-user from given social_network_id and webhook_id
                user_credential_obj = \
                    eventbrite_rsvp.get_user_credentials_by_webhook()

                # sets user credentials as a global variable
                eventbrite_rsvp.set_user_credential(user_credential_obj)

                # getting attendee data and appends social_network_rsvp_id in attendee
                #  object
                attendee = eventbrite_rsvp.get_attendee(rsvp)
                if attendee:
                    # base class method to pick the source product id for
                    # attendee
                    # and appends in attendee
                    attendee = eventbrite_rsvp.pick_source_product(attendee)

                    # base class method to store attendees's source event in
                    # candidate_source DB table
                    attendee = eventbrite_rsvp.save_attendee_source(attendee)

                    # base class method to save attendee as candidate in DB
                    # table candidate
                    attendee = eventbrite_rsvp.save_attendee_as_candidate(attendee)

                    # base class method to save rsvp data in DB table rsvp
                    attendee = eventbrite_rsvp.save_rsvp(attendee)

                    # base class method to save entry in candidate_event_rsvp
                    # DB table
                    attendee = eventbrite_rsvp.save_candidate_event_rsvp(attendee)

                    # base class method to save rsvp data in DB table activity
                    eventbrite_rsvp.save_rsvp_in_activity_table(attendee)
            elif action == 'test':
                print 'Successful Webhook Connection'
        except Exception as e:
            info_to_log = dict(error_message=e.message)
            log_exception(eventbrite_rsvp.traceback_info,
                          "Error Occurred while saving RSVP through webhook."
                          "%(error_message)s" % info_to_log)
            data = {'message': e.message,
                    'status_code': 500}
            return flask.jsonify(**data), 500

        data = {'message': 'RSVP Saved',
                'status_code': 200}
        return flask.jsonify(**data), 200
    else:
        # return hub_challenge, 200
        logger.warn('No RSVP Data')
        data = {'message': 'No RSVP Data',
                'status_code': 500}
        return flask.jsonify(**data), 500


def get_rsvp_id(url):
    """
    This gets the social_network_rsvp_id by comparing url of response of rsvp
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


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = json.dumps(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(ApiException)
def handle_invalid_usage(error):
    response = json.dumps(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(Exception)
def handle_invalid_usage(error):
    response = json.dumps(dict(message='Ooops! Internal server error occurred..'))
    response.status_code = 500
    return response


@app.teardown_request
def teardown_request(exception=None):
    db_session.remove()
