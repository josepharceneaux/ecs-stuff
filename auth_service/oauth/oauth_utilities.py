__author__ = 'ufarooqi'

import uuid
import os
from flask import request, jsonify
from dateutil.parser import parse
from datetime import datetime, timedelta
from flask_oauthlib.provider import OAuth2RequestValidator
from werkzeug.security import check_password_hash
from auth_service.common.models.user import User, Client, Token, db
from auth_service.common.redis_cache import redis_store
from auth_service.oauth import logger, app
from auth_service.common.error_handling import UnauthorizedError, InvalidUsage
from ..custom_error_codes import AuthServiceCustomErrorCodes as custom_errors
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

MAXIMUM_NUMBER_OF_INVALID_LOGIN_ATTEMPTS = 5


# TODO Once our flask services would be up we'll migrate all existing passwords to flask PBKDF format
def change_hashing_format(password):
    """
    This method compensates for difference between formats of PBKDF hashed password in web2py and flask
    :param str password: password of a user
    :rtype: str
    """
    if password is None:
        return ''
    elif password.count('$') == 2:
        (digest_alg, salt, hash) = password.split('$')
        return 'pbkdf2:sha512:1000$%s$%s' % (salt, hash)


def authenticate_user(username, password, *args, **kwargs):
    """
    It's user getter method i.e it'll retrieve a User object from database given valid username/password.
    If user provides a wrong password, his wrong login attempt counter in redis is incremented by 1.
    If wrong login attempt counter reaches 5 we disable the user. Wrong login attempt counter for each user
    is reset after every hour
    :param str username: username of a user
    :param str password:  password of a user
    :rtype: User
    """
    assert isinstance(username, basestring)
    assert isinstance(password, basestring)
    user = User.query.filter_by(email=username).first()
    if user and not user.is_disabled:
        user_password = change_hashing_format(user.password)
        if check_password_hash(user_password, password):
            return user
        else:
            if not redis_store.exists('invalid_login_attempt_counter_{}'.format(username)):
                redis_store.setex('invalid_login_attempt_counter_{}'.format(username), 1, 3600)
            else:
                previous_wrong_password_count = int(redis_store.get('invalid_login_attempt_counter_{}'.format(username)))
                if previous_wrong_password_count + 1 >= MAXIMUM_NUMBER_OF_INVALID_LOGIN_ATTEMPTS:
                    redis_store.delete('invalid_login_attempt_counter_{}'.format(username))
                    user.is_disabled = 1
                    db.session.commit()
                    logger.info("User %s has been disabled because %s invalid login attempts have been made in "
                                "last one hour", user.id, MAXIMUM_NUMBER_OF_INVALID_LOGIN_ATTEMPTS)
                    raise UnauthorizedError("User %s has been disabled because %s invalid login attempts have made in "
                                            "last one hour" % (user.id, MAXIMUM_NUMBER_OF_INVALID_LOGIN_ATTEMPTS))
                else:
                    time_to_live = redis_store.ttl('invalid_login_attempt_counter_{}'.format(username))
                    redis_store.setex('invalid_login_attempt_counter_{}'.format(username),
                                      previous_wrong_password_count + 1, time_to_live)

    logger.warn('There is no user with username: %s and password: %s', username, password)
    return None


def save_token_v2(user):
    """
    This method will create a new bearer token from authenticated user
    :param User user: Authenticated user object
    :rtype: dict
    """
    assert isinstance(user, User)
    current_date_time = datetime.utcnow()
    expires = current_date_time + timedelta(seconds=app.config['JWT_OAUTH_EXPIRATION'])
    expires_at = expires.strftime("%d/%m/%Y %H:%M:%S")

    secret_key_id = str(uuid.uuid4())[0:10]
    secret_key = os.urandom(24).encode('hex')
    redis_store.setex(secret_key_id, secret_key, app.config['JWT_OAUTH_EXPIRATION'])

    s = Serializer(secret_key, expires_in=app.config['JWT_OAUTH_EXPIRATION'])

    payload = dict(
        user_id=user.id,
        created_at=datetime.utcnow().isoformat()
    )

    user.last_login_datetime = datetime.utcnow()
    db.session.commit()

    return dict(
        user_id=user.id,
        access_token='%s.%s' % (s.dumps(payload), secret_key_id),
        expires_at=expires_at,
        token_type="Bearer"
    )


def verify_jwt(token, secret_key_id):
    """
    This method will authenticate/verify a json web token
    :param secret_key_id: Redis Key for SECRET-KEY
    :param token: JSON Web Token (JWT)
    :return:
    """

    s = Serializer(redis_store.get(secret_key_id) or '')

    try:
        data = s.loads(token)
    except BadSignature:
        raise UnauthorizedError("Your Token is not found", error_code=11)
    except SignatureExpired:
            raise UnauthorizedError("Your Token has expired", error_code=12)
    except Exception:
        raise UnauthorizedError("Your Token is not found", error_code=11)

    if data['user_id']:
        user = User.query.get(data['user_id'])
        if user:
            if user.password_reset_time <= parse(data['created_at']):
                return user
            else:
                redis_store.delete(secret_key_id)
                raise UnauthorizedError("Your token has expired due to password reset", error_code=12)

    raise UnauthorizedError(error_message="Your Token is invalid", error_code=13)


def authenticate_request():
    """
    This method will authenticate jwt in request headers
    :return: None
    """
    try:
        json_web_token = request.headers['Authorization'].replace('Bearer', '').strip()
        json_web_token = json_web_token.split('.')
        assert json_web_token.__len__() == 4

        secret_key_id = json_web_token.pop()
        json_web_token = '.'.join(json_web_token)

    except Exception as e:
        raise InvalidUsage("`Authorization` Header is missing or poorly formatted. Because: %s" % e.message)

    return secret_key_id, verify_jwt(json_web_token, secret_key_id)


def load_client(client_id):
    """
    It's a client getter method i.e it'll simply retrieve Client object from database given valid client_id
    :param int client_id: id of a client
    :rtype: Client
    """
    return Client.query.filter_by(client_id=client_id).first()


def load_token(access_token=None, refresh_token=None):
    """
    It's token getter method i.e it'll retrieve a Token object from database given valid access or refresh token
    :param str access_token: value of access_token of a user
    :param str refresh_token: value of refresh_token of a user
    :rtype: Token
    """
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()
    return None


def save_token_v1(token, request, *args, **kwargs):
    """
    This method will delete all old tokens of a user and will store new token in Token table
    :param dict[str | int] token: dictionary of different attributes of a bearer token
    :param Request request: flask request instance
    :rtype: Token
    """
    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=request.user.id
    ).all()
    latest_token = tokens.pop() if tokens else None

    # make sure that every client has only one token connected to a user
    for t in tokens:
        db.session.delete(t)

    db.session.commit()

    token['user_id'] = request.user.id
    if latest_token:
        try:
            if datetime.utcnow() < latest_token.expires:
                token['expires_at'] = latest_token.expires.strftime("%d/%m/%Y %H:%M:%S")
                token['access_token'] = latest_token.access_token
                token['refresh_token'] = latest_token.refresh_token
                return latest_token
            else:
                db.session.delete(latest_token)
                db.session.commit()
        except Exception:
            db.session.rollback()

    expires = datetime.utcnow() + timedelta(seconds=token.get('expires_in'))
    token['expires_at'] = expires.strftime("%d/%m/%Y %H:%M:%S")

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    db.session.add(tok)
    request.user.last_login_datetime = datetime.utcnow()

    db.session.commit()

    logger.info('Bearer token has been created for user %s', request.user.id)
    return tok


class GetTalentOauthValidator(OAuth2RequestValidator):
    """
    GetTalentOauthValidator is wrapper to flask-oauthlib native request validator to improve error messages
    """

    def __init__(self):
        self._clientgetter = load_client
        self._usergetter = authenticate_user
        self._tokengetter = load_token
        self._tokensetter = save_token_v1

    def validate_bearer_token(self, token, scopes, request):
        """
        This method will check existence and expiration of bearer token
        :param str token: value of access_token
        :param list[str] scopes:
        :param Request request: flask request instance
        :rtype: bool
        """
        tok = self._tokengetter(access_token=token)
        if not tok:
            request.error_message = 'Bearer Token is not found.'
            request.error_code = custom_errors.TOKEN_NOT_FOUND
            return True

        # validate expires
        if datetime.utcnow() > tok.expires:
            request.error_message = 'Bearer Token is expired. Please refresh it'
            request.error_code = custom_errors.TOKEN_EXPIRED
            return True

        # validate scopes
        if scopes and not set(tok.scopes) & set(scopes):
            request.error_message = 'Bearer Token scope is not Valid.'
            request.error_code = custom_errors.TOKEN_INVALID
            return True

        request.access_token = tok
        request.user = tok.user
        request.scopes = scopes

        if hasattr(tok, 'client'):
            request.client = tok.client
        elif hasattr(tok, 'client_id'):
            request.client = self._clientgetter(tok.client_id)
        return True

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        """Revoke an access or refresh token.
        """
        if token_type_hint:
            tok = self._tokengetter(**{token_type_hint: token})
        else:
            tok = self._tokengetter(access_token=token)
            if not tok:
                tok = self._tokengetter(refresh_token=token)

        if tok:
            tok.delete()
            return True
        request.error_message = "Invalid token supplied."
        return False