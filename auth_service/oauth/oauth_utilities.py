__author__ = 'ufarooqi'

from flask_oauthlib.provider import OAuth2RequestValidator
from werkzeug.security import check_password_hash
from auth_service.common.models.user import *
from auth_service.oauth import logger, app
from datetime import datetime, timedelta


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
    It's user getter method i.e it'll retrieve a User object from database given valid username/password
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
    secret_key = os.urandom(24)
    redis_store.setex(secret_key_id, secret_key, app.config['JWT_OAUTH_EXPIRATION'])
    s = Serializer(secret_key, expires_in=app.config['JWT_OAUTH_EXPIRATION'])

    payload = dict(
        user_id=user.id
    )
    return jsonify(dict(
        user_id=user.id,
        access_token=s.dumps(payload),
        expires_in=app.config['JWT_OAUTH_EXPIRATION'],
        expires_at=expires_at,
        token_type="Bearer",
        secret_key_id=secret_key_id
    ))


def verify_jw_token(secret_key_id, token):
    """
    This method will authenticate/verify a json web token
    :param secret_key_id: Redis key of SECRET_KEY
    :param token: JSON Web Token (JWT)
    :return:
    """
    s = Serializer(redis_store.get(secret_key_id) or '')
    try:
        data = s.loads(token)
    except SignatureExpired:
        raise UnauthorizedError(error_message="Your Token has been expired", error_code=12)
    except BadSignature:
        raise UnauthorizedError(error_message="Your Token is not found", error_code=11)
    except Exception:
        raise UnauthorizedError(error_message="Your Token is not found", error_code=11)

    if data['user_id']:
        user = User.query.get(data['user_id'])
        if user:
            return user

    raise UnauthorizedError(error_message="Your Token is invalid", error_code=13)


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
    if latest_token and datetime.utcnow() < latest_token.expires:
        token['expires_at'] = latest_token.expires.strftime("%d/%m/%Y %H:%M:%S")
        token['access_token'] = latest_token.access_token
        token['refresh_token'] = latest_token.refresh_token
        return latest_token
    else:
        if latest_token:
            db.session.delete(latest_token)
            db.session.flush()

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