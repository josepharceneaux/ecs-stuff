
__author__ = 'ufarooqi'

from werkzeug.security import gen_salt
from auth_service.oauth import app, logger
from auth_service.oauth import gt_oauth
from auth_service.common.error_handling import *
from auth_service.common.routes import AuthApi, AuthApiV2
from auth_service.common.models.user import Permission
from auth_service.common.models.user import User
from auth_service.oauth.oauth_utilities import (authenticate_user, save_token_v2,
                                                redis_store, authenticate_request, load_client, save_token_v1)


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


@app.route(AuthApiV2.TOKEN_REFRESH, methods=['POST'])
def refresh_token_v2():
    """ Refresh an access_token for a user """

    secret_key_id, authenticated_user = authenticate_request()

    if secret_key_id:
        redis_store.delete(secret_key_id)

    return save_token_v2(authenticated_user)


@app.route(AuthApiV2.TOKEN_REVOKE, methods=['POST'])
def revoke_token_v2():
    """ Revoke an access_token """
    secret_key_id, authenticated_user = authenticate_request()
    if secret_key_id:
        redis_store.delete(secret_key_id)
    return '', 200


@app.route(AuthApiV2.AUTHORIZE)
def authorize_v2():
    """ Authorize an access token which is stored in Authorization header """
    secret_key_id, authenticated_user = authenticate_request()
    return jsonify(user_id=authenticated_user.id)


@app.route(AuthApiV2.TOKEN_OF_ANY_USER)
def access_token_of_user_v2(user_id):
    """
    GET /users/<user_id>/access_token Create Access token for a user
    :param user_id: Id of user
    :return: A dictionary containing bearer token information for that user
    :rtype: dict
    """

    secret_key_id, authenticated_user = authenticate_request()
    user_permission = [permission.name for permission in authenticated_user.role.get_all_permissions_of_role()]

    if Permission.PermissionNames.CAN_IMPERSONATE_USERS not in user_permission:
        raise UnauthorizedError("User doesn't have appropriate permissions to perform this operation")

    user_object = User.query.get(user_id)

    if not user_object:
        raise NotFoundError("User with user_id %s doesn't exist" % user_id)

    return save_token_v2(user_object)


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


@app.route(AuthApi.TOKEN_OF_ANY_USER)
@gt_oauth.require_oauth()
def access_token_of_user(user_id):
    """
    GET /users/<user_id>/access_token?client_id=HpllhpiCXjokvk2djOinLvioudW6yh29qanD7Fu3 Create Access token for a user
    :param user_id: Id of user
    :return: A dictionary containing bearer token information for that user
    :rtype: dict
    """
    if hasattr(request.oauth, 'error_message'):
        error_message = request.oauth.error_message or ''
        if error_message:
            error_code = request.oauth.error_code or None
            raise UnauthorizedError(error_message=error_message, error_code=error_code)

    user_permission = [permission.name for permission in request.oauth.user.role.get_all_permissions_of_role()]

    if Permission.PermissionNames.CAN_IMPERSONATE_USERS not in user_permission:
        raise UnauthorizedError("User doesn't have appropriate permissions to perform this operation")

    client_id = request.args.get('client_id', '')
    user_object = User.query.get(user_id)

    if not user_object:
        raise NotFoundError("User with user_id %s doesn't exist" % user_id)

    request.client = load_client(client_id)
    if not request.client:
        raise NotFoundError("Either client_id is missing or invalid")

    request.user = user_object
    token = dict(
        access_token=gen_salt(30),
        refresh_token=gen_salt(30),
        token_type='Bearer',
        expires_in=app.config['JWT_OAUTH_EXPIRATION'],
        scope=''
    )

    save_token_v1(token, request)
    return jsonify(token), 200