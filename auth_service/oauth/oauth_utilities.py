__author__ = 'ufarooqi'
from flask_oauthlib.provider import OAuth2RequestValidator
from werkzeug.security import check_password_hash
from auth_service.common.models.user import *
from auth_service.oauth import logger
from datetime import datetime, timedelta


def load_client(client_id):
    """
    It's a client getter method i.e it'll simply retrieve Client object from database given valid client_id
    :param int client_id: id of a client
    :rtype: Client
    """
    return Client.query.filter_by(client_id=client_id).first()


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
        return 'pbkdf2:sha512:2000$%s$%s' % (salt, hash)


def get_user(username, password, *args, **kwargs):
    """
    It's user getter method i.e it'll retrieve a User object from database given valid username/password
    :param str username: username of a user
    :param str password:  password of a user
    :rtype: User
    """
    assert isinstance(username, basestring)
    assert isinstance(password, basestring)
    user = User.query.filter_by(email=username).first()
    if user:
        user_password = change_hashing_format(user.password)
        if check_password_hash(user_password, password):
            return user
    logger.warn('There is no user with username: %s and password: %s', username, password)
    return None


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


def save_token(token, request, *args, **kwargs):
    """
    This method will delete all old tokens of a user and will store new token in Token table
    :param dict[str | int] token: dictionary of different attributes of a bearer token
    :param Request request: flask request instance
    :rtype: Token
    """
    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=request.user.id
    )
    # make sure that every client has only one token connected to a user
    for t in tokens:
        db.session.delete(t)

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)
    token['expires_at'] = expires.strftime("%d/%m/%Y %H:%M:%S")
    token['user_id'] = request.user.id

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
    db.session.commit()
    logger.info('Bearer token has been created for user %s', request.user.id)
    return tok


class GetTalentOauthValidator(OAuth2RequestValidator):
    """
    GetTalentOauthValidator is wrapper to flask-oauthlib native request validator to improve error messages
    """

    def __init__(self):
        self._clientgetter = load_client
        self._usergetter = get_user
        self._tokengetter = load_token
        self._tokensetter = save_token

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
            request.error_code = 11
            return True

        # validate expires
        if datetime.utcnow() > tok.expires:
            request.error_message = 'Bearer Token is expired. Please refresh it'
            request.error_code = 12
            return True

        # validate scopes
        if scopes and not set(tok.scopes) & set(scopes):
            request.error_message = 'Bearer Token scope is not Valid.'
            request.error_code = 13
            return True

        request.access_token = tok
        request.user = tok.user
        request.scopes = scopes

        if hasattr(tok, 'client'):
            request.client = tok.client
        elif hasattr(tok, 'client_id'):
            request.client = self._clientgetter(tok.client_id)
        return True
