import json
import re
import flask
import types
import requests
from functools import wraps
from requests_oauthlib import OAuth2Session
from event_importer.base import logger
from event_importer.eventbrite import Eventbrite
from gt_models.event import Event
from gt_models.user import UserCredentials
from gt_models.social_network import SocialNetwork
from gt_models.config import db_session
from flask.ext.restful import Resource
from flask.ext.restful import Api, abort
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash

# configuration
from event_importer.utilities import log_exception, authenticate_user

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
OAUTH_SERVER = 'http://127.0.0.1:8888/oauth2/authorize'


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper

api.route = types.MethodType(api_route, api)


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


@app.route('/rsvp', methods=['GET'])
def handle_rsvp():
    """
    This function Only receives data when a candidate rsvp to some event.
    It first find the getTalent user having incoming webhook id.
    Then it creates the candidate in candidate table by getting information
    of attendee. Then it inserts in rsvp table the required information.
    It will also insert an entry in DB tables candidate_event_rsvp and activity
    """
    if request.data:
        # creating object of Eventbrite class
        eventbrite_rsvp = Eventbrite()
        try:
            data = json.loads(request.data)
            action = data['config']['action']
            if action == 'order.placed':
                webhook_id = data['config']['webhook_id']
                url_of_rsvp = str(json.loads(request.data)['api_url'])

                # gets dictionary object of vendor_rsvp_id
                rsvp = get_rsvp_id(url_of_rsvp)

                eventbrite_rsvp.webhook_id = webhook_id

                # getting data of gt-user of Get Talent
                # gets gt-user from given social_network_id and webhook_id
                user_credential_obj = \
                    eventbrite_rsvp.get_user_credentials_by_webhook()

                # sets user credentials as a global variable
                eventbrite_rsvp.set_user_credential(user_credential_obj)

                # getting attendee data and appends vendor_rsvp_id in attendee
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
        logger.warn('No RSVP Data')
        data = {'message': 'No RSVP Data',
                'status_code': 500}
        return flask.jsonify(**data), 500


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


def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if not getattr(func, 'authenticated', True):
                return func(*args, **kwargs)
            bearer = flask.request.headers.get('Authorization')
            access_token = bearer.lower().replace('bearer ', '')
            oauth = OAuth2Session(token={'access_token': access_token})
            response = oauth.get(OAUTH_SERVER)
            if response.status_code == 200 and response.json().get('user_id'):
                kwargs['user_id'] = response.json()['user_id']
                return func(*args, **kwargs)
            else:
                abort(401)
        except Exception as e:
            import traceback
            print traceback.format_exc()
            print 'Error....'
            print e.message
            abort(401)
    return wrapper


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class Resource(Resource):
    method_decorators = [authenticate]


@api.route('/events/')
class Events(Resource):
    """
        This resource returns a list of events or it can be used to create event using POST
    """
    @authenticate
    def get(self, **kwargs):
        """
        This action returns a list of user events.
        """
        # raise InvalidUsage('Not authorized', status_code=401)
        events = map(lambda event: event.to_json(), Event.query.filter_by(userId=kwargs['user_id']).all())
        if events:
            return {'events': events}, 200
        else:
            return {'events': []}, 200

    @authenticate
    def post(self, **kwargs):
        """
        This method takes data to create event in local database as well as on corresponding social network.
        :return: id of created event
        """
        # data = request.values
        return dict(id=1), 201


@api.route('/events/<int:event_id>')
class EventById(Resource):

    @authenticate
    def get(self, event_id, **kwargs):
        """
        Returns event object with required id
        :param id: integer, unique id representing event in GT database
        :return: json for required event
        """
        return dict(event={}), 200

    @authenticate
    def post(self, **kwargs):
        """
        Updates event in GT database and on corresponding social network
        :param id:
        """
        return None, 204

    @authenticate
    def delete(self, **kwargs):
        """
        Removes event from GT database and from social network as well.
        :param id: (Integer) unique id in Event table on GT database.
        """
        return None, 200


@api.route('/social_networks/')
class SocialNetworks(Resource):
    """
        This resource returns a list of social networks
    """

    def set_is_subscribed(self, dicts, value=False):
        for dict in dicts:
            dict['is_subscribed'] = value
        return dicts

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user events.
        """
        print args, kwargs
        user_id = kwargs.get('user_id') or None
        assert user_id
        # Get list of networks user is subscribed to from UserCredentials table
        subscribed_networks = None
        subscribed_data = UserCredentials.get_by_user_id(user_id=user_id)
        if subscribed_data:
            # Get list of social networks user is subscribed to
            subscribed_networks = SocialNetwork.get_by_ids(
                [data.socialNetworkId for data in subscribed_data]
            )
            # Convert it to JSON
            subscribed_networks = map(lambda sn: sn.to_json(), subscribed_networks)
            # Add 'is_subscribed' key in each object and set it to True because
            # these are the social networks user is subscribed to
            subscribed_networks = self.set_is_subscribed(subscribed_networks, value=True)
        # Get list of social networks user is not subscribed to
        unsubscribed_networks = SocialNetwork.get_all_except_ids(
            [data.socialNetworkId for data in subscribed_data ]
        )
        if unsubscribed_networks:
            unsubscribed_networks = map(lambda sn: sn.to_json(), unsubscribed_networks)
            # Add 'is_subscribed' key in each object and set it to False
            unsubscribed_networks = self.set_is_subscribed(unsubscribed_networks, value=False)
        # Now merge both subscribed and unsubscribed networks
        all_networks = []
        if subscribed_networks:
            all_networks.extend(subscribed_networks)
        if unsubscribed_networks:
            all_networks.extend(unsubscribed_networks)
        if all_networks:
            return {'social_networks': all_networks}
        else:
            return {'social_networks': []}

@app.teardown_request
def teardown_request(exception=None):
    db_session.remove()
