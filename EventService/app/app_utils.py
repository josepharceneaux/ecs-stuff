from functools import wraps
import flask
from flask.ext.restful import abort
from requests_oauthlib import OAuth2Session

OAUTH_SERVER = 'http://127.0.0.1:8888/oauth2/authorize'


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
        except:
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
