"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
import json
import traceback

# Initializing App. This line should come before any imports from models
from sms_campaign_service import init_app
app = init_app()

# Third party imports
import flask
from flask import request
from flask.ext.cors import CORS
from flask.ext.restful import Api
from werkzeug.utils import redirect

# Application specific imports
from restful.sms_campaign import sms_campaign_blueprint
from sms_campaign_service import logger
from social_network_service.utilities import http_request
from sms_campaign_service.utilities import url_conversion
from sms_campaign_service.utilities import send_sms_campaign
from sms_campaign_service.utilities import get_smart_list_ids
from sms_campaign_service.utilities import process_redirection
from sms_campaign_service.utilities import process_link_in_body_text
from sms_campaign_service.app.app_utils import ApiResponse
from sms_campaign_service.custom_exceptions import ApiException
from sms_campaign_service.common.error_handling import InternalServerError

# Register Blueprints for different APIs
app.register_blueprint(sms_campaign_blueprint)
api = Api(app)

LONG_URL = 'https://webdev.gettalent.com/web/user/login?_next=/web/default/angular#!/'

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
    return 'Welcome to SMS Campaign Service'


@app.route('/url_conversion', methods=['GET', 'POST'])
# @app.route('/url_conversion/<url>', methods=['GET', 'POST'])
def short_url_test(url=None):
    """
    This is a test end point which converts given URL to short URL
    :return:
    """
    url = 'http://127.0.0.1:8010/convert_url'
    response = http_request('GET', url, params={'url': LONG_URL})
    if response.ok:
        short_url, long_url = url_conversion(url)
        return redirect(short_url)
    else:
        data = {'message': 'No URL given in request',
                'status_code': 200}
    return flask.jsonify(**data), 200


# @app.task
@app.route('/sms', methods=['GET', 'POST'])
def sms_send():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    if request.args.has_key('text'):
        body_text = request.args['text']
        body_text = process_link_in_body_text(body_text)
    else:
        body_text = 'Welcome to getTalent, Please click on given link: %s' % LONG_URL
    ids = get_smart_list_ids()
    response = send_sms_campaign(ids, body_text)
    if response:
        return flask.jsonify(**response), response['status_code']
    else:
        raise InternalServerError


@app.route("/sms_receive", methods=['GET', 'POST'])
def sms_receive():
    """
    This is a test end point to receive sms
    :return:
    """
    if request.values:
        response = 'SMS received from %(From)s on %(To)s. Body text is "%(Body)s"' \
                   % request.values
        print response
    else:
        response = 'No SMS received'
    data = {'message': response,
            'status_code': 200}
    return flask.jsonify(**data)


@app.route('/redirect', methods=['GET', 'POST'])
def redirect_to_long_url():
    """
    This is a test end point which redirects to Long URL
    :return:
    """
    if request.args.get('url_id'):
        url_conversion = process_redirection(request.args['url_id'])
        return redirect(url_conversion.destination_url)
    else:
        return ''


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
    response = json.dumps(dict(message='Ooops! Internal server error occurred..' + str(error.message)))
    return ApiResponse(response, status=500)

