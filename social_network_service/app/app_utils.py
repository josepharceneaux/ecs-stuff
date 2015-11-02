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
from flask.ext.restful import Api
from requests_oauthlib import OAuth2Session
from social_network_service.common.error_handling import *
from social_network_service import logger
from flask import current_app as app


class CustomApi(Api):
    """
    This class extends error handling functionality for flask.restful.Api class.
    flask.restful.Api does not provide a good way of handling custom exceptions and
    returning dynamic response.

    In flask.restful.Api.handle_error(e) method, it just says "Internal Server Error" for
    our custom exceptions so we are overriding this method and now it raises again out custom
    exceptions which will be caught by error handlers in error_handling.py module.
     and if it is some other exception then actual method will handle it.
    """
    def handle_error(self, e):
        # if it is our custom exception or its subclass instance then raise it
        # so it error_handlers for app can catch this error and can send proper response
        # in required format

        # check whether this exception is some chile class of TalentError base class.
        # bases = [cls.__name__ for cls in e.__class__.__mro__]
        # if 'TalentError' in bases:
        if isinstance(e, TalentError):
            raise
        else:
            # if it is not a custom exception then let the Api class handle it.
            return super(CustomApi, self).handle_error(e)


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
            response = oauth.get(app.config['OAUTH_SERVER_URI'])
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
