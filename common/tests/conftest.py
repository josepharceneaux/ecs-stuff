
# this is where we can place fixtures that are required for testing some common programs such as
# user authentication, models, etc.

import pytest
import requests
import json
from flask import jsonify
from flask import request
from flask import current_app as app


class UserAuthentication():
    def __init__(self, **kwargs):
        pass

    def login(self, username, password):
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            return jsonify({'error': {'message': 'No Auth header set'}}), 400

        resp = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
        if resp.status_code != 200:
            return jsonify({'error': {'message': 'Invalid Authorization'}}), 401
        valid_user_id = json.loads(resp.text).get('user_id')
        if not valid_user_id:
            return jsonify({'error': {'message': 'Oauth did not provide a valid user_id'}}), 400


@pytest.fixture(scope='session')
def authentication():
    return UserAuthentication()