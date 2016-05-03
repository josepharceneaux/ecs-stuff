
__author__ = 'ufarooqi'

from auth_service.oauth import app
from auth_service.common.error_handling import *
from auth_service.common.routes import AuthApi
from auth_service.oauth.oauth_utilities import authenticate_user, save_token, verify_jw_token, redis_store


@app.route(AuthApi.TOKEN_CREATE, methods=['POST'])
def access_token():
    """ Create a new access_token for a user """
    body = request.form.to_dict()
    username = body.get('username', '')
    password = body.get('password', '')
    if not username or not password:
        raise InvalidUsage("Username or password is missing")
    else:
        authenticated_user = authenticate_user(username, password)
        if authenticated_user:
            return save_token(authenticated_user)
        else:
            raise UnauthorizedError("Incorrect username/password")


@app.route(AuthApi.TOKEN_REVOKE, methods=['POST'])
def revoke_token():
    """ Revoke an access_token """
    try:
        secret_key_id = request.headers['X-Talent-Secret-Key-ID']
        json_web_token = request.headers['Authorization'].replace('Bearer', '').strip()
    except KeyError:
        raise UnauthorizedError("`X-Talent-Secret-Key-ID` or `Authorization` Header is missing")

    verify_jw_token(secret_key_id, json_web_token)
    redis_store.delete(secret_key_id)
    return '', 204


@app.route(AuthApi.AUTHORIZE)
def authorize():
    """ Authorize an access token which is stored in Authorization header """
    try:
        secret_key_id = request.headers['X-Talent-Secret-Key-ID']
        json_web_token = request.headers['Authorization'].replace('Bearer', '').strip()
    except KeyError:
        raise UnauthorizedError("`X-Talent-Secret-Key-ID` or `Authorization` Header is missing")
    user = verify_jw_token(secret_key_id, json_web_token)
    return jsonify(user_id=user.id)
