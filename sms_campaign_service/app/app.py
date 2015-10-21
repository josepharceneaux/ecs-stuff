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
from flask.ext.cors import CORS
from flask.ext.restful import Api
from werkzeug.utils import redirect

# Application specific imports
from sms_campaign_service import logger
from sms_campaign_service.utilities import url_conversion
from sms_campaign_service.app.app_utils import ApiResponse
from sms_campaign_service.custom_exections import ApiException
from restful.sms_campaign import sms_campaign_blueprint

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
@app.route('/url_conversion/<url>', methods=['GET', 'POST'])
def short_url_test(url=None):
    """
    This is a test end point which converts given URL to short URL
    :return:
    """
    if url:
        short_url, long_url = url_conversion(url)
        data = {'short_url': short_url,
                'long_url': long_url,
                'status_code': 200}
    else:
        data = {'message': 'No URL given in request',
                'status_code': 200}
    return flask.jsonify(**data), 200
    # return redirectshort_url)


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

