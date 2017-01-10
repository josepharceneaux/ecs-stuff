"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
from datetime import datetime

# 3rd party imports
from flask import request, redirect, jsonify
from flask import send_from_directory
from flask.ext.graphql import GraphQLView

# Application specific imports
from social_network_service.modules.utilities import get_file_matches, get_test_info
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
from social_network_service.common.error_handling import InternalServerError, InvalidUsage
from social_network_service.common.routes import SocialNetworkApiUrl, SocialNetworkApi
from social_network_service.common.talent_config_manager import (TalentEnvs, TalentConfigKeys)
from social_network_service.common.utils.auth_utils import validate_jwt_token
from social_network_service.tasks import (import_eventbrite_event, process_meetup_event,
                                          process_meetup_rsvp, process_eventbrite_rsvp, run_tests)
from social_network_service.modules.constants import (MEETUP_CODE_LENGTH, ACTIONS, EVENTBRITE_USER_AGENT, EVENT, RSVP,
                                                      TEST_DIR, STATIC_DIR)


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
                logger.info('Successful webhook connection')
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


@app.route(SocialNetworkApi.TESTS, methods=['GET', 'POST'])
def tests():
    """
    This view gets user input and runs tests in background using celery task.
    It returns path / url to html report for given set of tests. You can see output / result of tests using
    that path in browser.

    You can call this endpoint using GET or POST request.

    Using GET request, we can specify an input string which will be matched with all tests and those tests will be run
    that contain given input string in test function name.
    We can also specify modules names (separated by comma) and then all tests inside those modules will be executed.

    If you want more control over selection of tests and also want to run more test using one api call, you can send
    a POST request with JSON data of this form
        {
            "module_name_without_py_extension": {
                "classes": {
                    "TestClass1": ["test_func_1", "test_func_2"],
                    "TestClass2": ["test_func_3, "test_func_4, "test_func_5"]
                },
                "functions": ["module_level_test_func_1", "module_level_test_func_2"]
            }
        }

    For SocialNetwork Service, here is a sample:
        {
             "test_v1_graphql_sn_api_tests": {
                "functions": [
                  "test_get_events_pagination",
                  "test_get_subscribed_social_network",
                  "test_get_venue"
                ]
              },
            "test_v1_importer": {
                "classes": {
                  "Test_Event_Importer": [
                    "test_eventbrite_rsvp_importer_endpoint"
                  ]
                },
                "functions": [
                  "test_event_import_to_update_existing_event",
                  "test_event_import_to_create_new_event"
                ]
              },
            "test_v1_organizer_api": {
                "classes": {
                  "TestOrganizers": ["test_get_with_valid_token"]
                }
            }
        }
    """
    token = request.args.get('token', '')
    validate_jwt_token(token)
    args = []
    if request.method == 'GET':
        """In GET request, we can select tests to run using name or module parameter.
            name will be matched with all test function names and those tests will be run those contain this name
            string in function name.
            Using module parameter you can run all tests in given module names. Multiple names are comma separated.
             /tests?modules=test_v1_organizer_api,test_v1_importer
        """
        name = request.args.get('name')
        modules = request.args.get('modules')
        if not (name or modules):
            raise InvalidUsage('You must specify test name or module name to run tests.')
        if modules:
            modules = modules.split(',')
            for module in modules:
                matches = get_file_matches(module + '.py', TEST_DIR)
                if len(matches) == 0:
                    raise InvalidUsage('There is no such test file with name "{}"'.format(module + '.py'))
                if len(matches) > 1:
                    raise InvalidUsage('There are multiple files in "tests" directory with name {}'.format(
                        module + '.py'))
                args.extend(matches)
        if name:
            """ To run test based on matching function name, specify name parameter. """
            args.extend([TEST_DIR, '-k', name])
    else:
        """ POST request """
        data = request.json
        for module_name in data:
            matches = get_file_matches(module_name + '.py', TEST_DIR)
            classes = data[module_name]['classes']
            functions = data[module_name]['functions']
            for class_name in classes:
                for function_name in classes[class_name]:
                    for module in matches:
                        args.append('{}::{}::{}'.format(module, class_name, function_name))
            for function_name in functions:
                for module in matches:
                    args.append('{}::{}'.format(module, function_name))

        if len(args) == 0:
            raise InvalidUsage('Invalid data. No test is selected to run.')

    assets = STATIC_DIR + '/{}'
    file_name = '{}{}'.format(datetime.utcnow().isoformat(), '.html')
    file_path = assets.format(file_name)
    with open(file_path, 'wb') as f:
        f.write('We are running your tests. Wait a moment')
        f.close()
    run_tests.delay(args, file_path)
    url = SocialNetworkApiUrl.ASSETS % file_name
    if request.args.get('redirect') == '1':
        return redirect(url)
    return jsonify({'output': url})


@app.route(SocialNetworkApi.ASSETS)
def static_files(path):
    """
    This view simply returns static files from "assets" directory for given path
    :param str path: path of file relative to assets folder
    """
    return send_from_directory(STATIC_DIR, path)


@app.route(SocialNetworkApi.TESTS_LIST)
def tests_info():
    """
    This view JOSN response containing all tests information which contains all test modules, classes and functions.
    """
    token = request.args.get('token', '')
    validate_jwt_token(token)
    return jsonify(get_test_info(TEST_DIR))
