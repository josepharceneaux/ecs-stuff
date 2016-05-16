
__author__ = 'ufarooqi'

from auth_service.oauth import app, logger
from auth_service.oauth import gt_oauth
from auth_service.common.error_handling import *
from auth_service.common.routes import AuthApi, AuthApiV2
from auth_service.oauth.oauth_utilities import authenticate_user, save_token_v2, verify_jw_token, redis_store


@app.route(AuthApiV2.TOKEN_CREATE, methods=['POST'])
def access_token_v2():
    """ Create a new access_token for a user """
    body = request.form.to_dict()
    username = body.get('username', '')
    password = body.get('password', '')
    if not username or not password:
        raise InvalidUsage("Username or password is missing")
    else:
        authenticated_user = authenticate_user(username, password)
        if authenticated_user:
            return save_token_v2(authenticated_user)
        else:
            raise UnauthorizedError("Incorrect username/password")


@app.route(AuthApiV2.TOKEN_REVOKE, methods=['POST'])
def revoke_token_v2():
    """ Revoke an access_token """
    try:
        secret_key_id = request.headers['X-Talent-Secret-Key-ID']
        json_web_token = request.headers['Authorization'].replace('Bearer', '').strip()
    except KeyError:
        raise UnauthorizedError("`X-Talent-Secret-Key-ID` or `Authorization` Header is missing")

    verify_jw_token(secret_key_id, json_web_token)
    redis_store.delete(secret_key_id)
    return '', 200


@app.route(AuthApiV2.AUTHORIZE)
def authorize_v2():
    """ Authorize an access token which is stored in Authorization header """
    try:
        secret_key_id = request.headers['X-Talent-Secret-Key-ID']
        json_web_token = request.headers['Authorization'].replace('Bearer', '').strip()
    except KeyError:
        raise UnauthorizedError("`X-Talent-Secret-Key-ID` or `Authorization` Header is missing")
    user = verify_jw_token(secret_key_id, json_web_token)
    return jsonify(user_id=user.id)


gt_oauth.grantgetter(lambda *args, **kwargs: None)
gt_oauth.grantsetter(lambda *args, **kwargs: None)


@app.route(AuthApi.TOKEN_CREATE, methods=['POST'])
@gt_oauth.token_handler
def access_token(*args, **kwargs):
    """ Create a new access_token for a user and store it in Token table """
    return None


@app.route(AuthApi.TOKEN_REVOKE, methods=['POST'])
@gt_oauth.revoke_handler
def revoke_token():
    """ Revoke or delete an access_token from Token table """
    pass


@app.route(AuthApi.AUTHORIZE)
@gt_oauth.require_oauth()
def authorize():
    """ Authorize an access token which is stored in Authorization header """
    if hasattr(request.oauth, 'error_message'):
        error_message = request.oauth.error_message or ''
        if error_message:
            error_code = request.oauth.error_code or None
            raise UnauthorizedError(error_message=error_message, error_code=error_code)
    user = request.oauth.user
    logger.info('User %s has been authorized to access getTalent api', user.id)
    return jsonify(user_id=user.id)