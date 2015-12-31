"""
This modules contains helper methods and classes which we are using in Social Network Service API app.

        * SocialNetworkApiResponse:
            This class is used to create API response object to return json response.

        * authenticate:
            This helper method is being used to annotate api endpoints and
            it gets user info from authorization token and then passes user_id
            in requested api endpoint method.
"""

from functools import wraps
import json
import flask
import traceback
from flask import Response
from requests_oauthlib import OAuth2Session
from social_network_service.common.error_handling import *
from social_network_service.common.routes import AuthApiUrl
from social_network_service import logger
from flask import current_app as app


class SocialNetworkApiResponse(Response):
    """
    Override default_mimetype to 'application/json' to return proper json api response
    """
    def __init__(self, response, status=200, content_type='application/json', headers=None):
        if isinstance(response, dict):
            response = json.dumps(response)
        super(Response, self).__init__(response, status=status, content_type=content_type, headers=headers)


def authenticate(func):
    """
    This helper method is being used to annotate api endpoints and
    it get user info from Authorization token and then passes user_id
    in requested api endpoint method.
    :param func: api endpoint method to be called
    :type func: function
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if not getattr(func, 'authenticated', True):
                return func(*args, **kwargs)
            bearer = flask.request.headers.get('Authorization')
            access_token = bearer.lower().replace('bearer ', '')
            oauth = OAuth2Session(token={'access_token': access_token})
            # db_data = Token.query.filter_by(access_token=access_token).first()
            response = oauth.get(AuthApiUrl.AUTH_SERVICE_AUTHORIZE_URI)
            if response.status_code == 200 and response.json().get('user_id'):
                kwargs['user_id'] = response.json()['user_id']
                return func(*args, **kwargs)
            else:
                # abort(401)
                raise UnauthorizedError('User not recognized. Invalid access token', error_code=401)
        except Exception as e:
            user_id = kwargs.get('user_id', 'Not given')
            logger.debug('User ID: %s\nError : %s\n\nTraceback: %s' % (
                user_id, e.message, traceback.format_exc()))
            raise
    return wrapper


def api_route(self, *args, **kwargs):
    """
    This method helps to make api endpoints to look similar to normal flask routes.
    Simply use it as a decorator on api endpoint method.

        :Example:

            @api.route('/events/')
            class Events(Resource):

                def get(*args, **kwargs):
                    do stuff here for GET request

                def post(*args, **kwargs):
                    do stuff here for POST request

    """
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper
