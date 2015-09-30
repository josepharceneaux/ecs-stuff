from functools import wraps
import flask
from flask import Response
from flask.ext.restful import abort
from requests_oauthlib import OAuth2Session

OAUTH_SERVER = 'http://127.0.0.1:8888/oauth2/authorize'


class ApiResponse(Response):
    """
    Override default_mimetype to 'application/json' to return proper json api response
    """
    def __init__(self, response, status=200, content_type='application/json', headers=None):
        super(Response, self).__init__(response, status=status, content_type=content_type, headers=headers)


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
            # import traceback
            # print traceback.format_exc()
            # print 'Error....'
            # print e.message
            # abort(401)
            raise
    return wrapper


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper