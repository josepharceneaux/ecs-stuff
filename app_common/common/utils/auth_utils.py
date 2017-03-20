"""Helper functions related to the authentication of GT users."""

__author__ = 'erikfarmer'

# Standard Library
import json
from functools import wraps
# Third Party
import requests
# Application/Module Specific
from ..utils.handy_functions import random_letter_digit_string
from flask import current_app as app
from ..models.user import *
from ..error_handling import *
from ..routes import AuthApiUrl, AuthApiUrlV2
from ..models.user import User, Role


def require_oauth(allow_null_user=False, allow_candidate=False):
    """
    This method will verify Authorization header of request using getTalent AuthService or Basic HTTP secret-key based
    Auth and will set request.user and request.oauth_token
    :param allow_null_user: Is user necessary for Authorization or not ?
    :param allow_candidate: Allow Candidate Id in JWT payload
    """

    def auth_wrapper(func):
        @wraps(func)
        def authenticate(*args, **kwargs):
            try:
                oauth_token = request.headers['Authorization']
            except KeyError:
                raise UnauthorizedError('You are not authorized to access this endpoint')

            if len(oauth_token.replace('Bearer', '').strip().split('.')) == 4:

                json_web_token = oauth_token.replace('Bearer', '').strip()
                json_web_token = json_web_token.split('.')
                secret_key_id = json_web_token.pop()
                json_web_token = '.'.join(json_web_token)
                User.verify_jw_token(secret_key_id, json_web_token, allow_null_user, allow_candidate)
                request.oauth_token = oauth_token
                return func(*args, **kwargs)

            # Olf OAuth2.0 based Authentication
            try:
                response = requests.get(AuthApiUrl.AUTHORIZE, headers={'Authorization': oauth_token})
            except Exception as e:
                raise InternalServerError(error_message=e.message)
            if response.status_code == 429:
                raise UnauthorizedError(error_message='You have exceeded the access limit of this API')
            elif not response.ok:
                error_body = response.json()
                if error_body['error']:
                    raise UnauthorizedError(error_message=error_body['error'].get('messagek', 'kamal'),
                                            error_code=error_body['error'].get('code', ''))
                else:
                    raise UnauthorizedError(error_message='You are not authorized to access this endpoint')
            else:
                valid_user_id = response.json().get('user_id')
                request.user = User.query.get(valid_user_id)
                request.oauth_token = oauth_token
                request.candidate = None
                return func(*args, **kwargs)

        return authenticate

    return auth_wrapper


def require_jwt_oauth(allow_null_user=False, allow_candidate=False):
    """
    This method will verify Authorization header of request using JWT based Authorization and
    will set request.user, request.oauth_token
    :param allow_null_user: Is user necessary for Authorization or not ?
    :param allow_candidate: Allow Candidate Id in JWT payload
    """

    def auth_wrapper(func):
        @wraps(func)
        def authenticate(*args, **kwargs):

            try:
                oauth_token = request.headers['Authorization']
            except KeyError:
                raise UnauthorizedError('You are not authorized to access this endpoint')

            json_web_token = oauth_token.replace('Bearer', '').strip()
            json_web_token = json_web_token.split('.')
            secret_key_id = json_web_token.pop()
            json_web_token = '.'.join(json_web_token)
            User.verify_jw_token(secret_key_id, json_web_token, allow_null_user, allow_candidate)
            request.oauth_token = oauth_token
            return func(*args, **kwargs)

        return authenticate

    return auth_wrapper


def require_role(role_name):
    """ This method ensures that user should have a certain role"""

    def roles(func):
        @wraps(func)
        def authenticate_role(*args, **kwargs):
            # For server-to-server Auth roles check should be skipped

            if not role_name:
                return func(*args, **kwargs)

            # TODO Investigate this code path
            if not request.user:
                return func(*args, **kwargs)

            role = request.user.role.name
            if role != role_name:
                raise UnauthorizedError(
                    error_message="User doesn't have appropriate permissions to "
                                  "perform this operation")
            return func(*args, **kwargs)

        return authenticate_role

    return roles


def require_all_permissions(*permission_names):
    """ This method ensures that user should have all permissions given in permission list"""

    def permissions(func):
        @wraps(func)
        def authenticate_permission(*args, **kwargs):
            # For server-to-server Auth roles check should be skipped

            if not permission_names:
                # Permission list is empty so it means func is not permission protected
                return func(*args, **kwargs)

            if not request.user:
                return func(*args, **kwargs)

            user_permissions = [permission.name for permission in request.user.role.get_all_permissions_of_role()]
            for permission_name in permission_names:
                if permission_name not in user_permissions:
                    raise UnauthorizedError(error_message="User doesn't have appropriate permissions to "
                                                          "perform this operation")

            request.user_permissions = user_permissions
            return func(*args, **kwargs)

        return authenticate_permission

    return permissions


def require_any_permission(*permission_names):
    """ This method ensures that user should have at least one permission given in permission list"""

    def permissions(func):
        @wraps(func)
        def authenticate_permission(*args, **kwargs):
            # For server-to-server Auth roles check should be skipped

            if not permission_names:
                # Permission list is empty so it means func is not permission protected
                return func(*args, **kwargs)

            if not request.user:
                return func(*args, **kwargs)

            user_permissions = [permission.name for permission in request.user.role.get_all_permissions_of_role()]

            authenticated_permissions = []
            for permission_name in permission_names:
                if permission_name in user_permissions:
                    authenticated_permissions.append(permission_name)

            if authenticated_permissions:
                request.user_permissions = user_permissions
                return func(*args, **kwargs)

            raise UnauthorizedError(error_message="User doesn't have appropriate permissions to "
                                                  "perform this operation")

        return authenticate_permission

    return permissions


def get_token_by_client_and_user(client_id, user_id, db):
    # Fetches an Oauth2 token given a client_id/user_id.
    token = db.session.query(Token).filter_by(client_id=client_id, user_id=user_id).first()
    if not token:
        token = create_token(client_id, user_id, db)
    return token


def create_token(client_id, user_id, db):
    # Creates an Oauth2 token given a client_id/user_id.
    token = Token(client_id=client_id, user_id=user_id, token_type='Bearer',
                  access_token=random_letter_digit_string(255),
                  refresh_token=random_letter_digit_string(255),
                  expires=datetime.datetime.utcnow() + datetime.timedelta(hours=2))
    db.session.add(token)
    db.session.commit()
    return token


def refresh_expired_token(token, client_id, client_secret):
    # Sends a refresh request to the Oauth2 server.
    payload = {'grant_type': 'refresh_token', 'client_id': client_id,
               'client_secret': client_secret, 'refresh_token': token.refresh_token}
    r = requests.post(AuthApiUrl.TOKEN_CREATE, data=payload)
    # TODO: Add bad request handling.
    return json.loads(r.text)['access_token']


def refresh_token(access_token):
    """
    This method takes a token (str) as input and then returns a new token after refreshing the expired one.
    :param access_token: auth token to be refreshed
    :param (Token | str) access_token: Token model instance or string token
    :return: Token
    """
    token = None
    if access_token and isinstance(access_token, basestring):
        token = Token.get_token(access_token=access_token)
        if not token:
            raise InternalServerError('No token object found for given access token: %s' % access_token)
    token = token if token else access_token
    if token and isinstance(token, Token):
        # Sends a refresh request to the Oauth2 server.
        data = {
            'client_id': token.client_id,
            'client_secret': token.client.client_secret,
            'refresh_token': token.refresh_token,
            'grant_type': u'refresh_token'
        }
        response = requests.post(AuthApiUrl.TOKEN_CREATE, data=data)
        assert response.status_code == requests.codes.OK, 'Unable to refresh user (id: %s) token. Error:%s' \
                                                          % (token.user.id, response.text)
        return response.json()['access_token']

    raise InvalidUsage('access_token must be instance of Token model or a string.')


def gettalent_generate_password_hash(new_password):
    """
    Wrapper around werkzeug.security.generate_password_hash

    :param str new_password: Password to hash according to gT security standards.
    :rtype: basestring
    """
    return generate_password_hash(new_password, method='pbkdf2:sha512:1000', salt_length=32)


def has_role(user, role):
    """
    Will return true if user has the specified role, otherwise false
    :type user: User
    :param role: A recognized user role such as: 'TALENT_ADMIN', 'DOMAIN_ADMIN'
    :rtype: bool
    """
    role_name = role.upper()
    accepted_roles = {role.name for role in Role.all()}
    assert role_name in accepted_roles, "User role not recognized: {role}. " \
                                        "User role must be one of the following: {roles}".format(
        role=role, roles=', '.join(accepted_roles))

    return user.role.name == role_name


def validate_jwt_token(token):
    """This function gets jwt token and validates. It raises 401 error if token is not valid"""
    token = token.split('.')
    secret_key_id = token.pop()
    json_web_token = '.'.join(token)
    User.verify_jw_token(secret_key_id, json_web_token)
